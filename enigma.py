# coding: utf-8
# python 3.8 x86_64

import string
import numpy as np


def list_char2int(l:list) -> list:
    return [ord(_) - 65 for _ in l]


class Enigma:
    rotors = {
        #        ABCDEFGHIJKLMNOPQRSTUVWXYZ
        "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
        "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
        "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
        "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
        "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z")
    }
    reflectors = {
        #     ABCDEFGHIJKLMNOPQRSTUVWXYZ
        "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
        "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL"
    }
    MODEL = "M3"

    def __init__(self, text:str="", rotors:tuple=("I", "II", "III"), fiches:tuple=(), reflector:str="B", positions:str="AAA", rings:tuple=(0, 0, 0)):
        self.text = tuple([(ord(c) - 65) if c in string.ascii_uppercase else c for c in text.upper()])
        self.text_int = tuple([(ord(c) - 65) for c in text.upper() if c in string.ascii_uppercase]) # to delete
        self.result = list()
        self.fiches = tuple([_.upper() for _ in fiches])
        self.reflector = reflector
        self.num_rotors = rotors
        self.rotors_position = positions
        self.rings_position = rings
        
        self._configuration()

    @property
    def result(self):
        return "".join(self._result)

    @result.setter
    def result(self, v=list()):
        self._result = v

    def _configuration(self):
        self._fiches = dict()
        for a,b in self.fiches:
            a, b = ord(a) - 65, ord(b) - 65
            self._fiches[a] = b
            self._fiches[b] = a

        self.rotor1 = Enigma.Rotor(*Enigma.rotors[self.num_rotors[0]], self.rotors_position[0], self.rings_position[0])
        self.rotor2 = Enigma.Rotor(*Enigma.rotors[self.num_rotors[1]], self.rotors_position[1], self.rings_position[1])
        self.rotor3 = Enigma.Rotor(*Enigma.rotors[self.num_rotors[2]], self.rotors_position[2], self.rings_position[2])
        self._reflector_charset = list_char2int(Enigma.reflectors.get(self.reflector))

    def reset(self):
        self._configuration()
        self.result = list()

    def substitution(self) -> None:
        for char in self.text:
            if isinstance(char, int):
                tmp = self._fiches.get(char, char)
                tmp = self._rotors_meca(tmp)
                tmp = self._fiches.get(tmp, tmp)
                self._result.append(chr(tmp + 65))
            else:
                self._result.append(char)

    def _rotors_meca(self, char:int) -> int:
        if self.rotor3.position == self.rotor3.notch:
            if self.rotor2.position == self.rotor2.notch:
                next(self.rotor1)
            next(self.rotor2)
        elif self.rotor2.position == self.rotor2.notch:
            next(self.rotor2)
            next(self.rotor1)
        next(self.rotor3)

        tmp = self.rotor3.enter(char)
        tmp = self.rotor2.enter(tmp)
        tmp = self.rotor1.enter(tmp)
        tmp = self._reflector_charset[tmp]
        tmp = self.rotor1.exit(tmp)
        tmp = self.rotor2.exit(tmp)
        tmp = self.rotor3.exit(tmp)
        return tmp
    
    def __repr__(self):
        r =  f"Rotors: {self.num_rotors}\n"
        r += f"Rotors init positions: {self.rotors_position}\n"
        r += f"Rings: {self.rings_position}\n"
        r += f"Reflector: {self.reflector}\n"
        r += "Stickers: {}\n".format(' '.join(self.fiches) or "no stickers")
        _ = chr(self.rotor1.position + 65) + chr(self.rotor2.position + 65) + chr(self.rotor3.position + 65)
        r += f"Rotors current positions: {_}"
        return r

    class Rotor:
        def __init__(self, charset:str, notch:str, position:str="A", ring:int=0):
            self.position = (ord(position) - 65) 
            self.notch = ord(notch) - 65
            self.ring = ring
            
            # calcul all combinaisons for enter and exit method
            self.rotor_charsets = [np.array(list_char2int(charset), dtype=np.int32)]
            self.rotor_charsets_index = [np.array([list_char2int(charset).index(c) for c in list_char2int(string.ascii_uppercase)], dtype=np.int32)]
            for i in range(25):
                tmp_charset = (self.rotor_charsets[i] - 1) % 26
                tmp_index = (self.rotor_charsets_index[i] -1) % 26
                tmp_charset = np.roll(tmp_charset, -1)
                tmp_index = np.roll(tmp_index, -1)
                self.rotor_charsets.append(tmp_charset)
                self.rotor_charsets_index.append(tmp_index)
            self.rotor_charsets = np.asarray(self.rotor_charsets)
            self.rotor_charsets_index = np.asarray(self.rotor_charsets_index)

        def __next__(self):
            self.position = (self.position + 1) % 26

        def enter(self, char:int) -> int:
            return self.rotor_charsets[(self.position - self.ring),char]

        def exit(self, char:int) -> int:
            return self.rotor_charsets_index[(self.position - self.ring), char]
