from __future__ import annotations
from typing import *


SPORTS_LUT = {"hockey":"hky", "basketball":"bball", "soccer":"soc", "baseball":"baseb", "softball":"softb", "lacrosse":"lax", "football":"fb", "fieldhockey":"fhky"}

SKIPPED_WORDS = {"the", "at", "in", "from", "over", "of", "and"}

GENDER_LUT = {
    "m":{"mens", "men", "m"},
    "w":{"womens", "women", "w"},
    "n":{"nongendered", "nongender", "none", "n"}
}



class SportAbbreviationError(Exception):
    pass
    
class SexError(Exception):
    pass


def _strip(st):
    return st.lower().strip().replace("\t","")
    
    
def _strong_strip(st):
    return _strip(st).replace(" ","")
    

class DefaultRplmFileRenderer:
    
    def __init__(self, *, school: str, sport: str, category: str, season: str) -> None:
        self.school = school
        self.sport = self._sport(sport)
        self.sex = self._sex(category)
        self.abbv = self._abbv(self.school)
        self.call = self._call(self.school, self.sport, self.sex)
    
    def suggested_filename(self) -> None | str:
        ...

    def render_player(self, *, first: str, last: str, num: str, posn: str) -> str:
        return "\t".join((
            f"{self.call}{num}",
            f"{self.school}'s {(x+', ')*bool(x)} {first} {last} ({num}), ",
            f"{first} {last} ({num}), ",
            f"{last}"
        ))
        """
        returns the output line into the exported  file for the player without newline
        "<call><num>\t<school>'s <pos,> <first> <last> (num), \t<first> <last> (<num>), \t<last>"
        """
        ...

    def render_coach(self, *, first: str, last: str, kind: str) -> str:
        """
        returns the output line into the exported  file for the coach
        """
        ...
    
    def _call(self, school, sport, sex):
        return abbv + sex + sport
        
    def _abbv(self, school):
        
        abbv = ""
        
        for word in school:
            if word in SKIPPED_WORDS:
                school.remove(word)
                
        for word in school:
            abbv += word[0].lower()
            
        return abbv
        
        
    def _sex(self, category):
        category = _strong_strip(category).replace("'","")
        # This is using the dictionary of sets to lookup the sex information. 
        for sex, inputs in GENDER_LUT:
            if category in inputs:
                return sex
        raise SexError("""Got {category}, need "men", "women", or "none".""")
    
        
    def _sport(self, sport: str) -> str:
        sport = _strong_strip(sport)
        if sport in SPORTS_LUT:
            return SPORTS_LUT[sport]
        raise SportsAbbreviationError("{sport} is not a valid option. Please try again. Allowed sports include: {set(SPORTS_LUT.keys())}")
            
    
