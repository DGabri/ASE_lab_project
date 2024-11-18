class Rates:
    def __init__(self, common_rate, rare_rate, super_rare_rate):
        self.common = common_rate
        self.rare = rare_rate
        self.super_rare = super_rare_rate

    def from_array(array):
        common_rate = array[0]
        rare_rate = array[1]
        super_rare_rate = array[2]
        return Rates(common_rate, rare_rate, super_rare_rate)
    
    def from_dict(dict):
        return Rates(dict['common'], dict['rare'], dict['super_rare'])

    def to_dict(self):

        return {
            'common': self.common,
            'rare': self.rare,
            'super_rare': self.super_rare
        }