
# Using machine learning to evaluate the best pick in a draft (League of Legends)

Under construction

## How to use

You need a developer API-KEY from https://developer.riotgames.com/. If you're API-KEY has expired at some point, just update the config.ini file.
You need also Python 3 and Tensorflow.

1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit.
2. DataDownloader.py : download raw game files according to the parameters you've chosen in config.ini.
3. DataExtractor.py : pre-process the data for the neural networks. 
4. Learner.py: under development

## Miscellaneous
- You can delete config.ini to start with a clean config. Just re-run ConfigUpdater.py.
- The download files are located in DATABASE/PATCH/REGION. Pre-processed data location is DATABASE/PATCH (data.cvs and extracted.txt)
- Once you have pre-processed all the data, you don't need to keep the data files and you can simpy delete the region folders (Only do this when there is no more data to download for the patch).
- The patch used for all the scripts is written in config.ini. It is updated to the lastest patch everytime ConfigUpdater.py is run. If you want to work on a specific patch, just edit config.ini.
(the list of patches is available at https://developer.riotgames.com/api-methods/#lol-static-data-v3/GET_getVersions)
