"""Tests for combat animations."""

import pytest
from reverie.animations import (
    AnimationType,
    AnimationFrame,
    Animation,
    AnimationPlayer,
    ANIMATIONS,
    get_animation,
    get_attack_animation,
    get_spell_animation,
    get_death_animation,
    render_animation_frame,
    create_combat_sequence,
)


class TestAnimationFrame:
    """Tests for AnimationFrame dataclass."""
    
    def test_frame_creation(self):
        """Test creating an animation frame."""
        frame = AnimationFrame(art="  *  ", duration_ms=100)
        assert frame.art == "  *  "
        assert frame.duration_ms == 100
    
    def test_default_duration(self):
        """Test default duration is 100ms."""
        frame = AnimationFrame(art="test")
        assert frame.duration_ms == 100
    
    def test_display_width(self):
        """Test width calculation."""
        frame = AnimationFrame(art="abc\ndefgh\nij")
        assert frame.display_width() == 5  # "defgh" is longest
    
    def test_display_height(self):
        """Test height calculation."""
        frame = AnimationFrame(art="line1\nline2\nline3")
        assert frame.display_height() == 3
    
    def test_single_line_dimensions(self):
        """Test single line frame dimensions."""
        frame = AnimationFrame(art="single")
        assert frame.display_width() == 6
        assert frame.display_height() == 1


class TestAnimation:
    """Tests for Animation dataclass."""
    
    def test_animation_creation(self):
        """Test creating an animation."""
        frames = [
            AnimationFrame("frame1", 50),
            AnimationFrame("frame2", 100),
        ]
        anim = Animation(name="Test", frames=frames)
        assert anim.name == "Test"
        assert len(anim.frames) == 2
        assert not anim.loop
    
    def test_total_duration(self):
        """Test total duration calculation."""
        frames = [
            AnimationFrame("a", 50),
            AnimationFrame("b", 100),
            AnimationFrame("c", 150),
        ]
        anim = Animation(name="Test", frames=frames)
        assert anim.total_duration_ms() == 300
    
    def test_frame_count(self):
        """Test frame count."""
        frames = [AnimationFrame("x") for _ in range(5)]
        anim = Animation(name="Test", frames=frames)
        assert anim.frame_count() == 5
    
    def test_empty_animation(self):
        """Test empty animation."""
        anim = Animation(name="Empty", frames=[])
        assert anim.total_duration_ms() == 0
        assert anim.frame_count() == 0


class TestAnimationRegistry:
    """Tests for animation registry."""
    
    def test_all_animation_types_registered(self):
        """Test all animation types have entries."""
        for anim_type in AnimationType:
            assert anim_type in ANIMATIONS
            assert isinstance(ANIMATIONS[anim_type], Animation)
    
    def test_get_animation(self):
        """Test getting animation by type."""
        anim = get_animation(AnimationType.ATTACK_SWORD)
        assert anim.name == "Sword Attack"
        assert anim.frame_count() > 0
    
    def test_animations_have_frames(self):
        """Test all animations have at least one frame."""
        for anim_type, anim in ANIMATIONS.items():
            assert anim.frame_count() > 0, f"{anim_type} has no frames"
    
    def test_animations_have_duration(self):
        """Test all animations have positive duration."""
        for anim_type, anim in ANIMATIONS.items():
            assert anim.total_duration_ms() > 0, f"{anim_type} has no duration"


class TestAttackAnimations:
    """Tests for attack animation helpers."""
    
    def test_sword_attack(self):
        """Test sword attack animation."""
        anim = get_attack_animation("sword")
        assert anim.name == "Sword Attack"
    
    def test_fist_attack(self):
        """Test fist attack animation."""
        anim = get_attack_animation("fist")
        assert anim.name == "Fist Attack"
    
    def test_unarmed_maps_to_fist(self):
        """Test unarmed uses fist animation."""
        anim = get_attack_animation("unarmed")
        assert anim.name == "Fist Attack"
    
    def test_magic_attack(self):
        """Test magic attack animation."""
        anim = get_attack_animation("magic")
        assert anim.name == "Magic Attack"
    
    def test_staff_maps_to_magic(self):
        """Test staff uses magic animation."""
        anim = get_attack_animation("staff")
        assert anim.name == "Magic Attack"
    
    def test_unknown_weapon_defaults_to_sword(self):
        """Test unknown weapon type defaults to sword."""
        anim = get_attack_animation("bazooka")
        assert anim.name == "Sword Attack"
    
    def test_case_insensitive(self):
        """Test weapon type is case insensitive."""
        anim = get_attack_animation("SWORD")
        assert anim.name == "Sword Attack"


class TestSpellAnimations:
    """Tests for spell animation helpers."""
    
    def test_fire_spell(self):
        """Test fire spell animation."""
        anim = get_spell_animation("fire")
        assert anim.name == "Fire Spell"
    
    def test_flame_maps_to_fire(self):
        """Test flame uses fire animation."""
        anim = get_spell_animation("flame")
        assert anim.name == "Fire Spell"
    
    def test_ice_spell(self):
        """Test ice spell animation."""
        anim = get_spell_animation("ice")
        assert anim.name == "Ice Spell"
    
    def test_frost_maps_to_ice(self):
        """Test frost uses ice animation."""
        anim = get_spell_animation("frost")
        assert anim.name == "Ice Spell"
    
    def test_lightning_spell(self):
        """Test lightning spell animation."""
        anim = get_spell_animation("lightning")
        assert anim.name == "Lightning Spell"
    
    def test_heal_spell(self):
        """Test heal spell animation."""
        anim = get_spell_animation("heal")
        assert anim.name == "Heal Spell"
    
    def test_unknown_element_defaults_to_fire(self):
        """Test unknown element defaults to fire."""
        anim = get_spell_animation("plasma")
        assert anim.name == "Fire Spell"


class TestDeathAnimations:
    """Tests for death animation helpers."""
    
    def test_normal_death(self):
        """Test normal death animation."""
        anim = get_death_animation(dramatic=False)
        assert anim.name == "Death Fade"
    
    def test_dramatic_death(self):
        """Test dramatic death animation."""
        anim = get_death_animation(dramatic=True)
        assert anim.name == "Dramatic Death"


class TestAnimationPlayer:
    """Tests for AnimationPlayer."""
    
    def test_player_creation(self):
        """Test creating a player."""
        player = AnimationPlayer()
        assert not player.is_playing()
    
    def test_player_with_custom_output(self):
        """Test player with custom output function."""
        outputs = []
        player = AnimationPlayer(output_func=outputs.append)
        
        frame = AnimationFrame("test", 10)
        anim = Animation("Test", [frame])
        player.play_inline(anim)
        
        assert len(outputs) > 0
        assert "test" in outputs[0]
    
    def test_stop_player(self):
        """Test stopping player."""
        player = AnimationPlayer()
        player._playing = True
        player.stop()
        assert not player.is_playing()


class TestRenderFrame:
    """Tests for frame rendering."""
    
    def test_center_in_width(self):
        """Test centering frame in width."""
        frame = AnimationFrame("ABC")
        rendered = render_animation_frame(frame, width=10)
        # "ABC" centered in 10 chars should have padding
        assert "ABC" in rendered
        assert len(rendered.split('\n')[0]) >= 3
    
    def test_multiline_centering(self):
        """Test multiline frame centering."""
        frame = AnimationFrame("AB\nCDEF")
        rendered = render_animation_frame(frame, width=10)
        lines = rendered.split('\n')
        assert len(lines) == 2
        assert "AB" in lines[0]
        assert "CDEF" in lines[1]


class TestCombatSequence:
    """Tests for combat sequence generation."""
    
    def test_hit_sequence(self):
        """Test creating a hit sequence."""
        seq = create_combat_sequence(
            attacker="Hero",
            defender="Goblin",
            attack_type=AnimationType.ATTACK_SWORD,
            hit=True,
            critical=False,
            fatal=False,
        )
        assert len(seq) == 2  # attack + impact
        assert seq[0][1] == "Hero attacks!"
        assert "Goblin is hit!" in seq[1][1]
    
    def test_miss_sequence(self):
        """Test creating a miss sequence."""
        seq = create_combat_sequence(
            attacker="Hero",
            defender="Goblin",
            attack_type=AnimationType.ATTACK_SWORD,
            hit=False,
        )
        assert len(seq) == 2  # attack + miss
        assert "dodges" in seq[1][1]
    
    def test_critical_hit_sequence(self):
        """Test creating a critical hit sequence."""
        seq = create_combat_sequence(
            attacker="Hero",
            defender="Goblin",
            attack_type=AnimationType.ATTACK_SWORD,
            hit=True,
            critical=True,
        )
        assert len(seq) == 2
        assert "CRITICAL HIT!" in seq[1][1]
    
    def test_fatal_hit_sequence(self):
        """Test creating a fatal hit sequence."""
        seq = create_combat_sequence(
            attacker="Hero",
            defender="Goblin",
            attack_type=AnimationType.ATTACK_SWORD,
            hit=True,
            fatal=True,
        )
        assert len(seq) == 3  # attack + impact + death
        assert "falls" in seq[2][1]
    
    def test_critical_fatal_sequence(self):
        """Test creating a critical fatal sequence."""
        seq = create_combat_sequence(
            attacker="Hero",
            defender="Boss",
            attack_type=AnimationType.ATTACK_MAGIC,
            hit=True,
            critical=True,
            fatal=True,
        )
        assert len(seq) == 3
        assert "CRITICAL" in seq[1][1]
        assert "falls" in seq[2][1]
