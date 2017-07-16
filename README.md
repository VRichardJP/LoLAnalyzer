
# Using machine learning to evaluate the best pick in a draft (League of Legends)

Under construction

## How to use

You need a developer API-KEY from https://developer.riotgames.com/. If you're API-KEY has expired at some point, just update the config.ini file.
You need also Python 3 and Tensorflow.

1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit.
2. DataDownloader.py : download raw game files according to the parameters you've chosen in config.ini (patch, regions, leagues).
3. DataExtractor.py : pre-process all the downloaded data (all patch, all regions)
4. Learner.py: under development

## Miscellaneous
- When there's a new patch, run ConfigUpdater.py
- You can delete config.ini to start with a clean config but it's easier to simply edit the file
- The downloaded games are located under DATABASE_ROOT/patches/PATCH/REGION/. You can change the patch/regions you're downloading games from by simply editing config.ini. 
- Pre-processed data location is DATABASE_ROOT/ (data.cvs and extracted.txt) and contains all the data you've downloaded (all patches/all regions)
- The models you train are located under DATABASE_ROOT/model.