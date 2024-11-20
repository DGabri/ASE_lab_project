class Piece:
    def __init__(self, piece_id, name, grade, pic, value, description):
        self.id = piece_id
        self.name = name
        self.grade = grade
        self.pic = pic
        self.value = value
        self.description = description

    def from_array(array):
        piece_id = array[0]
        name = array[1]
        grade = array[2]
        pic = array[3]
        value = array[4]
        description = array[5]
        return Piece(piece_id, name, grade, pic, value, description)

    def to_dict(self):
        return vars(self)