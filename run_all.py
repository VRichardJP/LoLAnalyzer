# All script can be called from here

import ConfigUpdater
import DataDownloader
import DataExtractor
import RoleUpdater
import DataProcessing
import DataShuffling
import Learner
import BestPicks

import Modes

image = False
permutation = False # not implemented
mode = Modes.BR_Mode(image, permutation)

if __name__ == '__main__':
    ConfigUpdater.run()
    DataDownloader.run(mode)
    DataExtractor.run(mode)
    RoleUpdater.run(mode)
    DataProcessing.run(mode)
    DataShuffling.run(mode)
    Learner.run(mode)

    # BestPicks.run(mode=mode, IMAGE=IMAGE, arch='Dense5', a_kwargs={'NN': 2048, 'training': False})
