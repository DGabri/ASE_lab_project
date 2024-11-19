from classes.rates import Rates

class Banner:
    def __init__(self, banner_id, name, cost, pic, pieces_num, rates):
        self.id = banner_id
        self.name = name
        self.cost = cost
        self.pic = pic
        self.pieces_num = pieces_num
        self.rates = rates

    def from_array(array):
        banner_id = array[0]
        name = array[1]
        cost = array[2]
        pic = array[3]
        pieces_num = array[4]
        rates = Rates.from_array(array[5])
        return Banner(banner_id, name, cost, pic, pieces_num, rates)
    
    def from_dict(dict):
        rates = Rates.from_dict(dict['rates'])
        return Banner(dict['id'], dict['name'], dict['cost'], dict['pic'], dict['pieces_num'], rates)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cost': self.cost,
            'pic': self.pic,
            'pieces_num': self.pieces_num,
            'rates': self.rates.to_dict()
        }