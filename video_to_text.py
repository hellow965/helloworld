#!/usr/bin/env python3
"""
视频语音转文本程序

这个程序可以从视频文件中提取音频，识别语音内容，并区分不同的说话者。
使用方法：python video_to_text.py <视频文件路径>
"""

import os
import sys
import tempfile
from pathlib import Path
import argparse
import torch
import whisper
from moviepy.editor import VideoFileClip
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook


def extract_audio_from_video(video_path, output_path=None):
    """从视频文件中提取音频"""
    if output_path is None:
        # 如果没有指定输出路径，创建临时文件
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "extracted_audio.wav")
    
    print(f"正在从视频中提取音频...")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_path, codec='pcm_s16le', verbose=False, logger=None)
    print(f"音频已提取到: {output_path}")
    return output_path


def transcribe_audio(audio_path, model_name="base"):
    """使用Whisper模型转录音频"""
    print(f"正在加载Whisper模型 ({model_name})...")
    model = whisper.load_model(model_name)
    
    print("正在转录音频...")
    result = model.transcribe(audio_path)
    
    return result


def get_speaker_diarization(audio_path):
    """使用pyannote.audio进行说话者分割"""
    print("正在加载说话者分割模型...")
    
    # 使用预训练的说话者分割模型
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=False
    )
    
    # 如果有GPU，使用GPU
    if torch.cuda.is_available():
        pipeline = pipeline.to(torch.device("cuda"))
    
    print("正在进行说话者分割...")
    with ProgressHook() as hook:
        diarization = pipeline(audio_path, hook=hook)
    
    return diarization


def combine_transcription_with_speakers(transcription, diarization):
    """将转录结果与说话者信息结合"""
    segments = []
    
    # 遍历转录的每个片段
    for segment in transcription["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        
        # 找出这个时间段内的主要说话者
        speakers_in_segment = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # 检查说话者片段与转录片段是否重叠
            if max(turn.start, start) < min(turn.end, end):
                overlap_duration = min(turn.end, end) - max(turn.start, start)
                if speaker in speakers_in_segment:
                    speakers_in_segment[speaker] += overlap_duration
                else:
                    speakers_in_segment[speaker] = overlap_duration
        
        # 获取主要说话者（说话时间最长的）
        main_speaker = max(speakers_in_segment.items(), key=lambda x: x[1])[0] if speakers_in_segment else "未知说话者"
        
        segments.append({
            "start": start,
            "end": end,
            "speaker": main_speaker,
            "text": text
        })
    
    return segments


def format_time(seconds):
    """将秒数格式化为时:分:秒格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def main():
    parser = argparse.ArgumentParser(description="从视频中提取语音文本并区分说话者")
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"], 
                        help="Whisper模型大小 (默认: base)")
    parser.add_argument("--output", help="输出文件路径 (默认: 与输入文件同名，但扩展名为.txt)")
    
    args = parser.parse_args()
    
    # 检查视频文件是否存在
    if not os.path.exists(args.video_path):
        print(f"错误: 找不到视频文件 '{args.video_path}'")
        return 1
    
    # 设置输出文件路径
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.video_path)
        output_path = str(input_path.with_suffix('.txt'))
    
    try:
        # 从视频中提取音频
        audio_path = extract_audio_from_video(args.video_path)
        
        # 转录音频
        transcription = transcribe_audio(audio_path, args.model)
        
        # 进行说话者分割
        diarization = get_speaker_diarization(audio_path)
        
        # 合并转录和说话者信息
        result = combine_transcription_with_speakers(transcription, diarization)
        
        # 写入结果到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            current_speaker = None
            for segment in result:
                # 只有当说话者变化时才打印说话者信息
                if segment["speaker"] != current_speaker:
                    current_speaker = segment["speaker"]
                    f.write(f"\n[{current_speaker}] ")
                
                # 写入文本
                f.write(f"{segment['text']} ")
                
            # 添加时间戳版本
            f.write("\n\n--- 详细时间戳版本 ---\n\n")
            for segment in result:
                start_time = format_time(segment["start"])
                end_time = format_time(segment["end"])
                f.write(f"[{start_time} --> {end_time}] [{segment['speaker']}]: {segment['text']}\n")
        
        print(f"\n转录完成! 结果已保存到: {output_path}")
        
        # 删除临时音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return 0
    
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())