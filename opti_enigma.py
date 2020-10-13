# coding: utf-8
# python 3.8 x86_64

import string
import numpy as np


def char2int(c:str) -> int:
    return ord(c) - 65


def int2char(i:int) -> str:
    return chr(i + 65)


def list_int2char(l:list) -> list:
    return [int2char(_) for _ in l]


def list_char2int(l:list) -> list:
    return [char2int(_) for _ in l]


class Enigma:    
    def __init__(self, text:str="", rotors:tuple=("I", "II", "III"), fiches:tuple=(), reflector:str="B", positions:str="AAA", ring:tuple=(0, 0, 0), d=False):
        self.alphabet = string.ascii_uppercase
        self.text = text.upper()
        self.result = list()
        self.fiches = tuple([list_char2int(_.upper()) for _ in fiches])
        self.reflector = reflector
        self.num_rotors = rotors
        self.rotors_position = positions
        self.ring_position = ring
        self._configuration()
        self.model = "M3"

    @property
    def result(self):
        return "".join(self._result)
        
    @result.setter
    def result(self, v=list()):
        self._result = v
    
    def _configuration(self) -> None:
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
        
        self.rotor1 = Enigma.Rotor(*rotors[self.num_rotors[0]], self.rotors_position[0], self.ring_position[0])
        self.rotor2 = Enigma.Rotor(*rotors[self.num_rotors[1]], self.rotors_position[1], self.ring_position[1])
        self.rotor3 = Enigma.Rotor(*rotors[self.num_rotors[2]], self.rotors_position[2], self.ring_position[2])
        self.reflector_charset = reflectors.get(self.reflector)
        self.current_pos = list_char2int(self.rotors_position)
    
    def reset(self) -> None:
        self._configuration()
        self.result = str()
        Enigma.log = str()

    def substitution(self) -> None:       
        for i, char in enumerate(self.text):
            if char in self.alphabet:
                tmp = self._plugboard(char2int(char))
                tmp = self._rotors_meca(tmp)
                tmp = self._plugboard(tmp)
                tmp = int2char(tmp)
                self._result.append(tmp) 
            else:
                self._result.append(char)
    
    def _plugboard(self, char) -> None:
        for fiche in self.fiches:
            if char in fiche:
                return fiche[(fiche.index(char) + 1) % 2]
        else:
            return char
    
    def _rotors_meca(self, char):
        if self.rotor3.is_notch():
            if self.rotor2.is_notch():
                next(self.rotor1)
            next(self.rotor2)
        elif self.rotor2.is_notch():
            next(self.rotor2)
            next(self.rotor1)
        next(self.rotor3)

        tmp = self.rotor3.enter(char)
        tmp = self.rotor2.enter(tmp)
        tmp = self.rotor1.enter(tmp)
        tmp = self._reflector(tmp)
        tmp = self.rotor1.exit(tmp)
        tmp = self.rotor2.exit(tmp)
        tmp = self.rotor3.exit(tmp)
        return tmp

    def _reflector(self, char:str) -> None:
        return char2int(self.reflector_charset[char]) % 26

    class Rotor:
        def __init__(self, charset:str, notch:str, position:str="A", ring:int=0):
            self.alphabet = tuple(list_char2int(string.ascii_uppercase))
            self.position = char2int(position)
            self.ring = ring
            self.notch = char2int(notch)
            
            # calcul of all combinaisons 
            self.rotor_charsets = [np.array(list_char2int(charset), dtype=np.int32)]
            for _ in range(25):
                tmp = (self.rotor_charsets[_] - 1) % 26
                tmp = np.append(tmp, tmp[0])
                tmp = np.delete(tmp, 0)
                self.rotor_charsets.append(tmp)
        
        def __next__(self):
            self.position = (self.position + 1) % 26

        def is_notch(self) -> bool:
            return self.position == self.notch
            
        def enter(self, char):
            return self.rotor_charsets[(self.position - self.ring) % 26][char]
        
        def exit(self, char):
            return  self.alphabet[tuple(self.rotor_charsets[(self.position - self.ring) % 26]).index(char)]
