from collections import Counter
from sc2reader.engine.events import PluginExit


class CompositionTracker(object):
    """
    Generates a list of Counter (a fancy dict) for each player that stores
    unit composition at regular intervals. This is stored as player.composition
    """
    name = 'CompositionTracker'

    # these pop up independently of units actually constructed
    EXCLUDED_NAMES = set([
        'ReaperPlaceholder',
        'Interceptor'
        'Locust',
        'LocustMP',
        'Broodling',
        'BroodlingEscort',  # the guys that fly with the Brood Lord
    ])

    def __init__(self, interval=15, remove_on_death=True, normalize_names=True):
        """
        interval defines how often we to extract compositions in seconds
        remove_on_death determines if they still count after dying
        normalize_names tries to fix up some awkward type names
        """
        self.frame_interval = interval << 4
        self.remove_on_death = remove_on_death
        self.normalize_names = normalize_names

    def handleEndGame(self, event, replay):
        for player in replay.players:
            unit_ranges = self.get_unit_ranges(player, replay.frames)

            player.compositions = [Counter() for i in
                    range(replay.frames // self.frame_interval + 1)]
            num_compositions = len(player.compositions)

            for name, start, end in unit_ranges:
                # if you are born on the frame exactly, you count. else, round up
                # if you die on the frame, you don't count. else, starting cutting it off
                start_index = (start - 1) // self.frame_interval + 1
                end_index = ((end - 1) // self.frame_interval + 1) if self.remove_on_death \
                        else num_compositions
                for index in range(start_index, end_index):
                    player.compositions[index][name] += 1

    def print_compositions(self, replay):
        """
        for debugging
        """
        for player in replay.players:
            for i, composition in enumerate(player.compositions):
                print(i * self.frame_interval / 16)
                print(composition)
                for unit, count in composition.items():
                    print('    {}\t\t{}'.format(unit, count))

    def get_unit_ranges(self, player, frames):
        """
        type history is usually just a single entry with the birthday, but sometimes it changes
        break history up into ranges with distinct types and store those
        the stuff about cur_ is trying to coalesce types when they just change the suffix
        """
        unit_ranges = []
        for unit in player.units:
            if unit.name.startswith('Beacon') or unit.name in self.EXCLUDED_NAMES or \
                    unit.hallucinated:
                continue

            intervals = unit.type_history.items()
            cur_name = self.normalize_type(intervals[0][1])
            cur_start = intervals[0][0]
            for interval in intervals[1:]:
                new_name = self.normalize_type(interval[1])
                if new_name != cur_name:
                    unit_ranges.append((cur_name, cur_start, interval[0]))
                    cur_name = new_name
                    cur_start = interval[0]

            unit_ranges.append((cur_name, cur_start, unit.died_at or frames))
        return unit_ranges

    def normalize_type(self, cur_type):
        """
        remove spurious type changes
        """
        name = cur_type.name

        if not self.normalize_names:
            return name

        for suffix in ('Flying', 'Lowered', 'Burrowed', 'Assault', 'Sieged', 'Uprooted'):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name

