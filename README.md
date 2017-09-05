
# Using machine learning to evaluate the best pick in a draft (League of Legends)

![demo](https://raw.githubusercontent.com/vingtfranc/LoLAnalyzer/master/demo.PNG)


Warning: I don't guarantee that all the scripts will run on your computer. You will need to install quite a bunch of big libraries to make it work. 

I know it would be cool to have a .exe to double-click, but python is not that easy to distribute, so I won't provide any executable

I may provide a demo network in a near future, but I can't maintain a network updated on a daily basis. I you want to seriously use this app you will have to train your own network. I would even recommend you to test and design your own networks.

## Why another tool? and why machine learning?
I am myself a LoL player. I play ranked a lot, and as many other players I want to become stronger. But becoming stronger is not all about picking Yasuo/Zed, making plays and carrying your team (of course don't forget to spam your champion mastery when you do). Sometimes, getting better at the game is simply about building a better team. Of course, you have your own preference: champions you like, champions you don't like. But how many times have you said to yourself you had lost a game by simply looking at your draft. Sometimes it's not your fault, you are first pick, you can't predict everything. But sometimes it is, and worse, you may not even realize it.

So how can you make sure you're not the fail pick?

Personally, I have been using op.gg for a long time. They provide a wide range of meaningful statistics for whoever wants to play ranked seriously. They give champions win ratio, matchups information, best builds, etc. But is it enough to choose the perfect champion for your team? Unfortunately, no. The reason is simple: since the analysis is made from large statistics, it does not take into account the most important information of a draft: what your team and the opponent team composition is. For instance, if you're top and op.gg says that Pantheon  has an average of 54.22% win rate and is the best top laner, but your team needs a tank, do you pick Pantheon anyway? The truth is that once you're in a draft, this number is not relevant anymore. 

My goal is simple: I want a system that can provide me a precise information on my draft, so I know what champion suits the current draft the best. And this is were machine learning is stronger than pure statistics. The strength of a machine learning based system is that it can predict the outcome of games it has never encounter, whereas a statistical tools need to see the same situation over and over to predict the outcome efficiently. How does it work? Well its rather simple: let's imagine your team is composed of Jarvan top, Sejuani jungle, Zilean mid, Janna support and that you won by picking Kog'maw adc. The system will not learn that Jarvan top, Sejuani jungle, Zilean mid, Janna support and Kog'maw adc is a good composition; instead, it will learn that this kind of team works well: a lot of cc, peels and one hyper-carry. You can replace Jarvan for Maokai, Sejuani for Amumu or Kog'Maw for Vayne, it doesn't chance the nature of the team, and from the neural network perspective, there are almost the same. Hence, the only thing you need to do is to make sure the neural networks has been trained in a lot of different drafts, so it understands what are the characteristics of each champion and what is needed in all kind of situations


## Requirements

You need at least (pip/google is your best friend):
- Python 3 
- Keras/Tensorflow (GPU version recommended if your graphic card is compatible)
- PyQt5
- A developer API-KEY from https://developer.riotgames.com/. If your API-KEY has expired at some point, just get a new one and update the config.ini file.

...and maybe some others libraries, just google/pip if something is missing.

## How to use

1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit. You can also use the one provided as example.
2. RunAll.py : All the steps from 2 to 8 at once. You can comment steps you've already done (especially if ou just want to run the program)

Or in details:
1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit. It determines most of the scripts behaviour.
2. PlayersListing.py : list all the players that meet the level requirements (defined in config.ini). This step is really long if you don't limit yourself to top leagues (challenger & master). I would not recommend to take more than challenger and master if you don't have a decent limit-rate on your API key.
3. DataDownloader.py : download raw game files played by the listed players
4. DataExtractor.py : extract and collect all the downloaded data
5. DataProcessing.py : pre-process the extrated data
6. DataShuffling.py : shuffling the data
7. Learner.py: train a neural network
8. BestPick.py: a very simple GUI so you can enter your draft and the role you want


## Folder tree

If you plan to go ahead with the example files, keep in mind you have to respect the following architecture: (if you start from scratch the tree will be created automaticaly)
From YOUR_DATABASE (defined in config.ini):  
    .  
    +-- data_ABR_TJMCS  
    |   +-- data_X  
    |   +-- ...  
    +-- extracted  
    |   +-- data_X  
    |   +-- ...  
    +-- models  
    |   +-- ABR_TJMCS_DenseUniform_5_1024.h5  
    +-- patches  
    +-- playerListing  
    +-- testing_ABR_TJMCS  
    |   +-- data_X  
    |   +-- ...  
    +-- training_ABR_TJMCS  
    |   +-- data_X  
    |   +-- ...  
    +-- extracted  


## Miscellaneous
- When there's a new patch, run ConfigUpdater.py
- You can delete config.ini to start with a clean config but it's easier to simply edit the file
- You can download games from several patches by listing them in the config.ini file. See the list of all the patches for the synthax and existing patches. In order to download the most recent games first the patches should be ordered from the most recent to the oldest. 
- When you download games, you may experience some errors (see https://developer.riotgames.com/response-codes.html), most often: 404/503 if the data was not found/service is unavailable, 403 means your API-KEY has expired (edit config.ini with a new one from https://developer.riotgames.com/).
- The downloaded games are located under DATABASE_ROOT/patches/PATCH/REGION/. You can change the patch/regions you're downloading games from by simply editing config.ini. 
- Extracted data location is DATABASE_ROOT/extracted/ and DATABASE_ROOT/extracted.txt and contains all the data you've downloaded (all patches/all regions)
- Preprocessed data location is DATABASE_ROOT/data_XXXX/.
- Only DATABASE_ROOT/training_XXXX/ is used for the training, so if you need to free some space on your hard drive you can delete the data files from a patch you've already fully extracted (under DATABASE_ROOT/patches/). Keep in mind if you don't configure the app properly, it may re-download games you've already used for training
- The models you train are located under DATABASE_ROOT/models.
