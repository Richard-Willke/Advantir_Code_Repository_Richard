
to take evvery image out from video to look at the black area
-ffmpeg -i Remove.mp4 -vf fps=1 out%d.png

to crop out the black area XX:XX:XX:XX cropsizeX:cropsizeY:startcropX:startcropY
-ffmpeg -i Remove.mp4 -filter:v "crop=1174:933:442:73" -c:a copy Remove3.mp4

-ffmpeg -i Ready.mp4 -filter:v "crop=1918:933:1:73" -c:a copy Ready3.mp4

scale the video:
-ffmpeg -i Remove3.mp4  -vf scale=iw/4.5:-1 Remove2.mp4 

-ffmpeg -i Ready3.mp4 -vf scale=iw/4.52:-1 Ready2.mp4
