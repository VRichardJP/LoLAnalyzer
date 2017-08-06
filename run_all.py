import ConfigUpdater
import DataDownloader
import DataExtractor
import RoleUpdater
import DataProcessing
import DataShuffling
import Learner

MODES = ['ABOTJMCS', 'ABOT']
MODE = 'ABOT'
IMAGE = True
# would generate a tremendous amount of data: 2 * 2^10 + 4 = 2052 per game. Currently its 2 * 10 + 4 = 24
# HENCE NOT IMPLEMENTED
PERMUTATIONS = False

if __name__ == '__main__':
    # ConfigUpdater.run()
    # DataDownloader.run()
    # DataExtractor.run(MODE, PERMUTATIONS)
    # RoleUpdater.run(MODE)  # not in ABOT mode
    DataProcessing.run(MODE, IMAGE)
    DataShuffling.run()
    Learner.run(MODE, IMAGE)
