"""ASCII combat animations for Reverie.

Provides frame-by-frame ASCII art animations for combat events.
Each animation is a sequence of frames that can be displayed with timing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional
import time


class AnimationType(Enum):
    """Types of combat animations."""
    ATTACK_SWORD = "attack_sword"
    ATTACK_MAGIC = "attack_magic"
    ATTACK_FIST = "attack_fist"
    DEFEND_BLOCK = "defend_block"
    DEFEND_DODGE = "defend_dodge"
    SPELL_FIRE = "spell_fire"
    SPELL_ICE = "spell_ice"
    SPELL_LIGHTNING = "spell_lightning"
    SPELL_HEAL = "spell_heal"
    DEATH_FADE = "death_fade"
    DEATH_DRAMATIC = "death_dramatic"
    HIT_IMPACT = "hit_impact"
    MISS = "miss"
    CRITICAL = "critical"


@dataclass
class AnimationFrame:
    """A single frame of an animation."""
    art: str
    duration_ms: int = 100
    
    def display_width(self) -> int:
        """Get the width of the widest line in the frame."""
        lines = self.art.strip().split('\n')
        return max(len(line) for line in lines) if lines else 0
    
    def display_height(self) -> int:
        """Get the number of lines in the frame."""
        return len(self.art.strip().split('\n'))


@dataclass
class Animation:
    """A complete animation sequence."""
    name: str
    frames: list[AnimationFrame]
    loop: bool = False
    
    def total_duration_ms(self) -> int:
        """Get total animation duration in milliseconds."""
        return sum(frame.duration_ms for frame in self.frames)
    
    def frame_count(self) -> int:
        """Get number of frames."""
        return len(self.frames)


# --- Attack Animations ---

ATTACK_SWORD_FRAMES = [
    AnimationFrame("""
      /|
     / |
    /  |
   /   |
  /    |
 /_____|
    """, 80),
    AnimationFrame("""
    ___
   /   \\
  |     |----->
   \\___/
    """, 60),
    AnimationFrame("""
           *
    ___   /|\\
   /   \\  |||
  |     |--X-->
   \\___/  |||
          \\|/
           *
    """, 120),
    AnimationFrame("""
    ___
   /   \\
  |     |
   \\___/
    """, 80),
]

ATTACK_FIST_FRAMES = [
    AnimationFrame("""
   _____
  |     |
  | o o |
  |  _  |
  |_____|
     |
    """, 80),
    AnimationFrame("""
   _____
  |     |    ___
  | o o |   /   \\
  |  _  |--( POW )
  |_____|   \\___/
     |
    """, 100),
    AnimationFrame("""
         * * *
   _____  \\|/
  |     |--*--
  | > < |  /|\\
  |  o  | * * *
  |_____|
     |
    """, 120),
    AnimationFrame("""
   _____
  |     |
  | ^ ^ |
  |  _  |
  |_____|
     |
    """, 80),
]

ATTACK_MAGIC_FRAMES = [
    AnimationFrame("""
    . * .
   . * * .
  . * @ * .
   . * * .
    . * .
    """, 100),
    AnimationFrame("""
   .* * *.
  .* * * *.
 .* * @ * *.
  .* * * *.
   .* * *.
    """, 80),
    AnimationFrame("""
  ** * * **
 ** * * * **
** * (!) * **
 ** * * * **
  ** * * **
    """, 60),
    AnimationFrame("""
 *** * * ***
*** * * * ***
** * [!] * **=======>>>>
*** * * * ***
 *** * * ***
    """, 120),
    AnimationFrame("""
              *
             /|\\
     ~~~~~~~~X~~~~~~~~~
             \\|/
              *
    """, 100),
]

# --- Defense Animations ---

DEFEND_BLOCK_FRAMES = [
    AnimationFrame("""
   _____
  |     |
  | o o |
  |  _  |
  |_____|
    """, 60),
    AnimationFrame("""
  [=====]
  [     ]
  [ o o ]   -->
  [  _  ]
  [=====]
    """, 80),
    AnimationFrame("""
  [=====]
  [#####]    *CLANG*
  [#o#o#]   <--X
  [##_##]
  [=====]
    """, 150),
    AnimationFrame("""
  [=====]
  [     ]
  [ - - ]
  [  _  ]
  [=====]
    """, 80),
]

DEFEND_DODGE_FRAMES = [
    AnimationFrame("""
      |
   ___|___
  |       |
  | o   o |   -->
  |   _   |
  |_______|
    """, 60),
    AnimationFrame("""
            |
         ___|___
        |       |
  -->   | o   o |
        |   _   |
        |_______|
    """, 80),
    AnimationFrame("""
               |
            ___|___
  ---->    |       |
           | ^   ^ |   *whoosh*
           |   o   |
           |_______|
    """, 100),
    AnimationFrame("""
      |
   ___|___
  |       |
  | ^   ^ |
  |   v   |
  |_______|
    """, 80),
]

# --- Spell Effect Animations ---

SPELL_FIRE_FRAMES = [
    AnimationFrame("""
      .
     /|\\
    """, 60),
    AnimationFrame("""
     ,*,
    /|||\\
   / ||| \\
    """, 80),
    AnimationFrame("""
    ,***,
   /|||||\\
  / ||||| \\
 /  |||||  \\
    """, 100),
    AnimationFrame("""
   ,*****,
  /|||||||\\
 /|||||||||\\
/   FIRE   \\
 \\|||||||/
  \\|||||/
   \\||/
    """, 150),
    AnimationFrame("""
  ~ ~ ~ ~ ~
   ~ * ~ * ~
  ~ * * * ~ 
   ~ ~ ~ ~
    """, 100),
]

SPELL_ICE_FRAMES = [
    AnimationFrame("""
      *
    """, 60),
    AnimationFrame("""
    * * *
     \\|/
    --+--
     /|\\
    * * *
    """, 80),
    AnimationFrame("""
   *  *  *
  * \\ | / *
    --+--
  * / | \\ *
   *  *  *
    """, 100),
    AnimationFrame("""
  * * * * *
 * \\\\|// *
   ==+==
 * //|\\\\ *
  * * * * *
   FREEZE!
    """, 150),
    AnimationFrame("""
  [=======]
  [  ~~~  ]
  [~~~~~~~]
  [  ~~~  ]
  [=======]
    """, 100),
]

SPELL_LIGHTNING_FRAMES = [
    AnimationFrame("""
     |
    """, 40),
    AnimationFrame("""
     |
     /
    |
    """, 40),
    AnimationFrame("""
     |
     /
    |
     \\
      |
    """, 40),
    AnimationFrame("""
     |
     /
    |
     \\
      |--ZAP!
     /
    |
    """, 60),
    AnimationFrame("""
     #
     /
    #
     \\
      #===***
     /
    #
    """, 100),
    AnimationFrame("""
     
    ***
   *****
    ***
     
    """, 80),
]

SPELL_HEAL_FRAMES = [
    AnimationFrame("""
      +
    """, 80),
    AnimationFrame("""
      +
    + + +
      +
    """, 100),
    AnimationFrame("""
      +
   +  +  +
  + + + + +
   +  +  +
      +
    """, 120),
    AnimationFrame("""
    ~~~~~
   ~ + + ~
  ~ + + + ~
   ~ + + ~
    ~~~~~
   HEALED
    """, 150),
    AnimationFrame("""
   *****
  *  +  *
 *   +   *
  *  +  *
   *****
    """, 100),
]

# --- Death Animations ---

DEATH_FADE_FRAMES = [
    AnimationFrame("""
   _____
  |     |
  | x x |
  |  o  |
  |_____|
    """, 100),
    AnimationFrame("""
   _____
  |  .  |
  | . . |
  |  .  |
  |_____|
    """, 100),
    AnimationFrame("""
   . . .
  .     .
  .     .
  .     .
   . . .
    """, 100),
    AnimationFrame("""
    . .
   .   .
   .   .
    . .
    """, 100),
    AnimationFrame("""
     .
    . .
     .
    """, 100),
    AnimationFrame("""
     
    """, 100),
]

DEATH_DRAMATIC_FRAMES = [
    AnimationFrame("""
   _____
  |     |
  | X X |
  |  O  |   ARGH!
  |_____|
     |
    / \\
    """, 120),
    AnimationFrame("""
   _____
  |     |  \\
  | X X |   \\
  |  O  |    \\
  |_____|     \\
     |         *
    / \\
    """, 100),
    AnimationFrame("""
            _____
           |     |
           | X X |
           |  O  |
           |_____|
              |
             / \\
    """, 100),
    AnimationFrame("""
    
        ___________
       |___________|
       |  X    X   |
       |_____O_____|
    """, 150),
    AnimationFrame("""
    
    
       ~~~~~~~~~~~
       ~ R.I.P.  ~
       ~~~~~~~~~~~
    """, 200),
]

# --- Impact Animations ---

HIT_IMPACT_FRAMES = [
    AnimationFrame("""
     *
    """, 40),
    AnimationFrame("""
    \\|/
   --*--
    /|\\
    """, 60),
    AnimationFrame("""
   \\\\|//
  --=*=--
   //|\\\\
    """, 80),
    AnimationFrame("""
  * * * *
   *HIT!*
  * * * *
    """, 100),
    AnimationFrame("""
    ~~~
    """, 60),
]

MISS_FRAMES = [
    AnimationFrame("""
    -->
    """, 60),
    AnimationFrame("""
        -->
    """, 60),
    AnimationFrame("""
            -->  ?
    """, 80),
    AnimationFrame("""
                 *whoosh*
    """, 100),
    AnimationFrame("""
      MISS!
    """, 120),
]

CRITICAL_FRAMES = [
    AnimationFrame("""
    *
    """, 40),
    AnimationFrame("""
    ***
   *****
    ***
    """, 60),
    AnimationFrame("""
   *****
  *******
 *********
  *******
   *****
    """, 80),
    AnimationFrame("""
  *********
 ***CRIT!***
*****!!!*****
 ***CRIT!***
  *********
    """, 150),
    AnimationFrame("""
    ~~~~~
   ~     ~
  ~       ~
   ~     ~
    ~~~~~
    """, 100),
]


# --- Animation Registry ---

ANIMATIONS: dict[AnimationType, Animation] = {
    AnimationType.ATTACK_SWORD: Animation("Sword Attack", ATTACK_SWORD_FRAMES),
    AnimationType.ATTACK_FIST: Animation("Fist Attack", ATTACK_FIST_FRAMES),
    AnimationType.ATTACK_MAGIC: Animation("Magic Attack", ATTACK_MAGIC_FRAMES),
    AnimationType.DEFEND_BLOCK: Animation("Block", DEFEND_BLOCK_FRAMES),
    AnimationType.DEFEND_DODGE: Animation("Dodge", DEFEND_DODGE_FRAMES),
    AnimationType.SPELL_FIRE: Animation("Fire Spell", SPELL_FIRE_FRAMES),
    AnimationType.SPELL_ICE: Animation("Ice Spell", SPELL_ICE_FRAMES),
    AnimationType.SPELL_LIGHTNING: Animation("Lightning Spell", SPELL_LIGHTNING_FRAMES),
    AnimationType.SPELL_HEAL: Animation("Heal Spell", SPELL_HEAL_FRAMES),
    AnimationType.DEATH_FADE: Animation("Death Fade", DEATH_FADE_FRAMES),
    AnimationType.DEATH_DRAMATIC: Animation("Dramatic Death", DEATH_DRAMATIC_FRAMES),
    AnimationType.HIT_IMPACT: Animation("Hit Impact", HIT_IMPACT_FRAMES),
    AnimationType.MISS: Animation("Miss", MISS_FRAMES),
    AnimationType.CRITICAL: Animation("Critical Hit", CRITICAL_FRAMES),
}


def get_animation(animation_type: AnimationType) -> Animation:
    """Get an animation by type."""
    return ANIMATIONS[animation_type]


def get_attack_animation(weapon_type: str = "sword") -> Animation:
    """Get appropriate attack animation for weapon type."""
    weapon_map = {
        "sword": AnimationType.ATTACK_SWORD,
        "fist": AnimationType.ATTACK_FIST,
        "unarmed": AnimationType.ATTACK_FIST,
        "magic": AnimationType.ATTACK_MAGIC,
        "staff": AnimationType.ATTACK_MAGIC,
        "wand": AnimationType.ATTACK_MAGIC,
    }
    anim_type = weapon_map.get(weapon_type.lower(), AnimationType.ATTACK_SWORD)
    return ANIMATIONS[anim_type]


def get_spell_animation(spell_element: str = "fire") -> Animation:
    """Get appropriate spell animation for element."""
    element_map = {
        "fire": AnimationType.SPELL_FIRE,
        "flame": AnimationType.SPELL_FIRE,
        "ice": AnimationType.SPELL_ICE,
        "frost": AnimationType.SPELL_ICE,
        "cold": AnimationType.SPELL_ICE,
        "lightning": AnimationType.SPELL_LIGHTNING,
        "thunder": AnimationType.SPELL_LIGHTNING,
        "electric": AnimationType.SPELL_LIGHTNING,
        "heal": AnimationType.SPELL_HEAL,
        "healing": AnimationType.SPELL_HEAL,
        "restore": AnimationType.SPELL_HEAL,
    }
    anim_type = element_map.get(spell_element.lower(), AnimationType.SPELL_FIRE)
    return ANIMATIONS[anim_type]


def get_death_animation(dramatic: bool = False) -> Animation:
    """Get death animation."""
    anim_type = AnimationType.DEATH_DRAMATIC if dramatic else AnimationType.DEATH_FADE
    return ANIMATIONS[anim_type]


class AnimationPlayer:
    """Plays animations with timing control."""
    
    def __init__(self, output_func: Optional[Callable[[str], None]] = None):
        """Initialize player with optional output function.
        
        Args:
            output_func: Function to call with each frame's art.
                        Defaults to print().
        """
        self.output_func = output_func or print
        self._playing = False
    
    def play(self, animation: Animation, clear_between: bool = True) -> None:
        """Play an animation synchronously.
        
        Args:
            animation: The animation to play.
            clear_between: Whether to clear screen between frames.
        """
        self._playing = True
        
        for frame in animation.frames:
            if not self._playing:
                break
            
            if clear_between:
                # ANSI escape to clear screen
                self.output_func("\033[2J\033[H")
            
            self.output_func(frame.art)
            time.sleep(frame.duration_ms / 1000.0)
        
        self._playing = False
    
    def play_inline(self, animation: Animation) -> None:
        """Play animation inline without clearing.
        
        Args:
            animation: The animation to play.
        """
        self._playing = True
        
        for frame in animation.frames:
            if not self._playing:
                break
            
            self.output_func(frame.art)
            time.sleep(frame.duration_ms / 1000.0)
        
        self._playing = False
    
    def stop(self) -> None:
        """Stop current animation."""
        self._playing = False
    
    def is_playing(self) -> bool:
        """Check if animation is currently playing."""
        return self._playing


def render_animation_frame(frame: AnimationFrame, width: int = 40) -> str:
    """Render a single frame centered in a given width.
    
    Args:
        frame: The frame to render.
        width: Total width to center in.
    
    Returns:
        Centered frame string.
    """
    lines = frame.art.strip().split('\n')
    centered_lines = []
    
    for line in lines:
        padding = (width - len(line)) // 2
        centered_lines.append(' ' * max(0, padding) + line)
    
    return '\n'.join(centered_lines)


def create_combat_sequence(
    attacker: str,
    defender: str,
    attack_type: AnimationType,
    hit: bool,
    critical: bool = False,
    fatal: bool = False,
) -> list[tuple[Animation, str]]:
    """Create a sequence of animations for a combat exchange.
    
    Args:
        attacker: Name of the attacker.
        defender: Name of the defender.
        attack_type: Type of attack animation.
        hit: Whether the attack hit.
        critical: Whether it was a critical hit.
        fatal: Whether the attack was fatal.
    
    Returns:
        List of (animation, caption) tuples.
    """
    sequence = []
    
    # Attack animation
    attack_anim = ANIMATIONS.get(attack_type, ANIMATIONS[AnimationType.ATTACK_SWORD])
    sequence.append((attack_anim, f"{attacker} attacks!"))
    
    if hit:
        # Impact
        if critical:
            sequence.append((ANIMATIONS[AnimationType.CRITICAL], "CRITICAL HIT!"))
        else:
            sequence.append((ANIMATIONS[AnimationType.HIT_IMPACT], f"{defender} is hit!"))
        
        # Death if fatal
        if fatal:
            sequence.append((ANIMATIONS[AnimationType.DEATH_DRAMATIC], f"{defender} falls!"))
    else:
        sequence.append((ANIMATIONS[AnimationType.MISS], f"{defender} dodges!"))
    
    return sequence
