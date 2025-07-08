# 视频语音转文本工具

这个工具可以从视频文件中提取音频，识别语音内容，并区分不同的说话者。它使用了以下技术：

- **MoviePy**: 从视频中提取音频
- **OpenAI Whisper**: 进行语音识别
- **Pyannote.Audio**: 进行说话者分割（区分不同的人）

## 安装依赖

在使用此工具前，需要安装以下依赖：

```bash
pip install moviepy openai-whisper pyannote.audio
```

## 使用方法

基本用法：

```bash
python video_to_text.py <视频文件路径>
```

高级选项：

```bash
python video_to_text.py <视频文件路径> --model <模型大小> --output <输出文件路径>
```

参数说明：
- `<视频文件路径>`: 要处理的视频文件路径
- `--model`: Whisper模型大小，可选值为 tiny, base, small, medium, large（默认为base）
- `--output`: 输出文件路径（默认为与输入文件同名，但扩展名为.txt）

## 输出格式

输出文件包含两种格式的转录结果：

1. **对话格式**：按说话者组织的文本，适合阅读
   ```
   [说话者_1] 这是第一个说话者说的话...
   
   [说话者_2] 这是第二个说话者的回应...
   ```

2. **时间戳格式**：包含详细时间信息的格式，适合精确引用
   ```
   [00:00:01.500 --> 00:00:05.200] [说话者_1]: 这是第一个说话者说的话...
   [00:00:05.300 --> 00:00:08.100] [说话者_2]: 这是第二个说话者的回应...
   ```

## 注意事项

1. 处理大型视频文件可能需要较长时间
2. 语音识别和说话者分割的准确性取决于音频质量
3. 使用更大的Whisper模型（如medium或large）可以提高识别准确性，但会消耗更多资源
4. 首次运行时会下载模型文件，需要网络连接

## 示例

```bash
# 使用基本模型处理视频
python video_to_text.py my_video.mp4

# 使用小型模型并指定输出文件
python video_to_text.py interview.mp4 --model small --output interview_transcript.txt

# 使用大型模型获取更高准确度
python video_to_text.py important_meeting.mp4 --model large
```