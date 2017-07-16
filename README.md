
# Using machine learning to evaluate the best pick in a draft (League of Legends)

Under construction

## How to use

You need a developer API-KEY from https://developer.riotgames.com/. If you're API-KEY has expired at some point, just update the config.ini file.
You need also Python 3 and Tensorflow.

1. ConfigUpdater.py : generate your personnal config.ini file. It is a simple text file and easy to edit. You can also delete it to generate a new one from scratch.
2. DataDownloader.py : download raw game files according to the parameters you've chosen in config.ini. Data location is DATABASE/PATCH/REGION
3. DataExtractor.py : pre-process the data for the neural networks. Data location is DATABASE/PATCH. If you want to regenerate the data from scratch, just delete data.cvs and extracted.txt
4. Learner.py: under development