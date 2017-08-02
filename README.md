
# Using machine learning to evaluate the best pick in a draft (League of Legends)

Warning: I don't guarantee that all the scripts will run on your computer. You will need to install quite a bunch of big libraries to make it work. 

I know it would be cool to have a .exe to double-click, but python is not that easy to distribute, so I won't provide any executable

I may provide a demo network in a near future, but I can't maintain a network updated on a daily basis. I you want to seriously use this app you will have to train your own network. I would even recommend you to test and design your own networks.

## Requirements

You need at least (pip/google is your best friend):
- Python 3 
- Tensorflow (GPU version recommended if your graphic card is compatible)
- PyQt5
- A developer API-KEY from https://developer.riotgames.com/. If your API-KEY has expired at some point, just get a new one and update the config.ini file.

...and maybe some others libraries, just google/pip if something is missing.

## How to use

1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit
2. DataDownloader.py : download raw game files according to the parameters in config.ini (patches, regions, leagues)
3. DataExtractor.py : extract and collect all the downloaded data
4. DataProcessing.py : pre-process the extrated data
5. DataShuffling.py : shuffling the data
6. Learner.py: train a neural network
7. BestPick.py: a very simple GUI so you can enter your draft and the role you want

If you're on Windows and lazy, you can use run_all.bat to do all the steps as once (you can comment lines by adding :: in the file).  

## Miscellaneous
- When there's a new patch, run ConfigUpdater.py
- You can delete config.ini to start with a clean config but it's easier to simply edit the file
- You can download games from several patches by listing them in the config.ini file. See the list of all the patches for the synthax and existing patches. In order to download the most recent games first the patches should be ordered from the most recent to the oldest. 
- When you download games, you may experience some errors (see https://developer.riotgames.com/response-codes.html), most often: 404/503 if the data was not found/service is unavailable, 403 means your API-KEY has expired (edit config.ini with a new one from https://developer.riotgames.com/).
- The downloaded games are located under DATABASE_ROOT/patches/PATCH/REGION/. You can change the patch/regions you're downloading games from by simply editing config.ini. 
- Extracted data location is DATABASE_ROOT/extracted/ and DATABASE_ROOT/extracted.txt and contains all the data you've downloaded (all patches/all regions)
- Preprocessed data location is DATABASE_ROOT/data/. The pre-processing can take a lot of time
- Only DATABASE_ROOT/shuffled/ is used for the training, so if you need to free some space on your hard drive you can delete the data files from a patch you've already fully extracted (under DATABASE_ROOT/patches/). Keep in mind if you don't configure the app properly, it may re-download games you've already used for training
- The models you train are located under DATABASE_ROOT/model.
