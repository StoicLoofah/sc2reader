import sc2reader

from sc2reader.plugins.gameheart import GameHeartNormalizer

sc2reader.register_plugin('Replay', GameHeartNormalizer())

replay = sc2reader.load_replay('gameheart.SC2Replay')

print '\n\nGAME 2'
replay = sc2reader.load_replay('gh_sameteam.SC2Replay')
