# Dependencies:
- [FFmpeg Essentials]([url](https://ffmpeg.org/))

Download FFmpeg, unzip, and copy the path to ffmpeg.exe (should be in the bin folder). Win + r to sysdm.cpl, select Advanced -> Environment Variables -> Path -> Edit -> New -> paste ffmpeg.exe path and save. Run ```ffmpeg -version``` in your terminal, a successful installation will return version info.
- [Pydub]([url](https://github.com/jiaaro/pydub))

Simply ```pip install pydub``` in your terminal and you should be good to go!
#  
ForzIVRadio takes any .mp3, .wav, or .ogg files and combines them with DJ commentary for a 100% game-realistic custom radio station!
To use ForzIVRadio, drag and drop your desired music tracks into the "music" folder and run. Your immersive playlist will pop out as a single .wav in the "output" folder.
DJ volume, music volume, fade length, etc. can be configured at the top of the script. For the best experience, I recommend using no more than 30 44.1Hz-96Hz audio files at a time.
Current release is far from complete, I just wanted to put something out here to start tracking progress. Sorry if your favorite DJ isn't on here yet, they will be soon! (there are literally hundreds of voice lines for me to sort by DJs / seasons)

# To do (in order):
- Populate DJ audio options (more than the current 3)
- Sort Mr. Jam's voicelines into seasons, implement season selector
- Repeat for all DJs, implement DJ selector
- Improve shuffle algorithm (DJ + music files)
- Repeat DJ lines if # of songs exceeds
