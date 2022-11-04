import os
from datetime import *
from moviepy.editor import VideoFileClip,CompositeVideoClip
PATH='/Users/tfproduct01/Documents/videos/'
custom_padding = 2.0
filelist=[x for x in os.listdir(PATH) if x.endswith('.mp4')]
clips=[]
for i in range(0,len(filelist)):
    if i==0:
        clips.append(VideoFileClip(PATH+filelist[0]).subclip(0, 5))
    else:
        clips.append(VideoFileClip(PATH+filelist[i]).subclip(0, 5).crossfadein(custom_padding))
final_clip = CompositeVideoClip(clips)
final_clip.write_videofile(PATH+'result/'+ datetime.now().strftime('%m%d_%H%M')+".mp4")