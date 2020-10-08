# coding: utf-8
# python 3.8 x86_64


import string
import numpy as np


def coroutine(func):
    def wrapper(*arg, **kwargs):
        generator = func(*arg, **kwargs)
        next(generator)
        return generator
    return wrapper


def char2int(c:str) -> int:
    return ord(c) - 65


def int2char(i:int) -> str:
    return chr(i + 65)


def list_int2char(l:list) -> list:
    return [int2char(_) for _ in l]


def list_char2int(l:list) -> list:
    return [char2int(_) for _ in l]


class Enigma:
    log = str()

    def __init__(self, text:str, rotors:tuple=("I", "II", "III"), fiches:tuple=(), reflector:str="B", positions:str="AAA", ring:tuple=(0, 0, 0), d=False):
        self.alphabet = string.ascii_uppercase
        self.text = text.upper()
        self.result = str()
        self.fiches = tuple([_.upper() for _ in fiches])
        self.reflector = reflector
        self.num_rotors = rotors
        self.rotors_position = positions
        self.ring_position = ring
        self.debug = d
        self._configuration()
        self.model = "M3"
        

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
        
        self._fiches = tuple([list_char2int(_) for _ in self.fiches])
        
        light = self._light()
        rotor1 = Enigma.Rotor(self.num_rotors[0], *rotors[self.num_rotors[0]], self.rotors_position[0], self.ring_position[0])
        rotor2 = Enigma.Rotor(self.num_rotors[1], *rotors[self.num_rotors[1]], self.rotors_position[1], self.ring_position[1])
        rotor3 = Enigma.Rotor(self.num_rotors[2], *rotors[self.num_rotors[2]], self.rotors_position[2], self.ring_position[2])
        reflector = self._reflector(reflectors.get(self.reflector), rotor1)
        rotor1.targets = {"enter": reflector, "exit": rotor2}
        rotor2.targets = {"enter": rotor1, "exit": rotor3}
        rotor3.targets = {"enter": rotor2, "exit": self._plugboard(light)}
        self._gen_plugboard = self._plugboard(rotor3)

    def reset(self) -> None:
        self._configuration()
        self.result = str()
        Enigma.log = str()

    def substitution(self) -> None:       
        for i, char in enumerate(self.text):
            if char in self.alphabet:
                Enigma.log += f"[+] char indice: {i}\n[+] input: {char}\n"
                self._gen_plugboard.send(("enter", char2int(char), True))
            else:
                self.result += char
        
        if self.debug:
            with open("Enigma_log.txt", mode="w") as fp:
                fp.write(Enigma.log)
    
    @coroutine
    def _plugboard(self, target) -> None:
        while True:
            cnx, char, stepping = yield
            for fiche in self._fiches:
                if char in fiche:
                    char_swap = fiche[(fiche.index(char) + 1) % 2]
                    Enigma.log += f"[+] connexion, plugboard {cnx}: {int2char(char_swap)}\n"
                    target.send((cnx, char_swap, stepping))
                    break
            else:
                Enigma.log += f"[+] no connexion, plugboard {cnx}: {int2char(char)}\n"
                if cnx == "enter":
                    Enigma.log += f"[+] base alphabet -> {self.alphabet}\n"
                target.send((cnx, char, stepping))
    
    @coroutine
    def _reflector(self, charset:str, target) -> None:
        while True:
            cnx, char, _ = yield
            r_char = char2int(charset[char]) % 26
            Enigma.log += f"[+] reflector  -> {int2char(r_char)}, {charset}\n"
            target.send(("exit", r_char, False))

    @coroutine
    def _light(self) -> None:
        while True:
            cnx, char, _ = yield
            Enigma.log += f"[+] light: {int2char(char)}\n"
            self.result += int2char(char)
            Enigma.log += "=" * 100 + "\n"
    
    class Rotor:
        def __init__(self, n:str, charset:str, notch:str, position:str="A", ring:int=0):
            self.num = n
            self.alphabet = tuple(list_char2int(string.ascii_uppercase))
            self.position = char2int(position)
            self.ring = ring
            self.notch = char2int(notch)
            self.targets = None
            
            # calcul of all combinaisons 
            self.rotor_charsets = [np.array(list_char2int(charset), dtype=np.int32)]
            for _ in range(25):
                tmp = (self.rotor_charsets[_] - 1) % 26
                tmp = np.append(tmp, tmp[0])
                tmp = np.delete(tmp, 0)
                self.rotor_charsets.append(tmp)
         
        def send(self, data:tuple) -> None:
            cnx, char, stepping = data
            
            if stepping:
                if self.notch != self.position:
                    stepping = False
                self.position = (self.position + 1) % 26
            elif cnx != "exit" and self.notch == self.position:
                self.position = (self.position + 1) % 26
                stepping = True
            
            if cnx == "enter":    
                wired_char = self.rotor_charsets[(self.position - self.ring) % 26][char]
            elif cnx == "exit":
                wired_char = self.alphabet[tuple(self.rotor_charsets[(self.position - self.ring) % 26]).index(char)]
            
            Enigma.log += (
                f"[+] {self.num:3}, {cnx:5} -> {int2char(wired_char)}, {''.join(list_int2char(self.rotor_charsets[self.position]))}"
                f", position: {int2char(self.position)}\n"
                )
            self.targets[cnx].send((cnx, wired_char, stepping))
