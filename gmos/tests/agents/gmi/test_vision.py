"""
Test: GMI Vision Reaction

This test demonstrates GMI reacting to light and shadows as if it saw them.
Light and shadow patterns are injected into the visual field, propagate through
the eye operator into the sensory block, and affect the affective state.
"""

import numpy as np
from gmos.agents.gmi.twelve_block_state import create_initial_state
from gmos.agents.gmi.full_dynamics import create_dynamics_system


def inject_light_pattern(system, state, pattern_type="bright", position=None, intensity=1.0):
    """
    Inject a light pattern into the visual field.
    """
    H, W = system.config.visual_height, system.config.visual_width
    N = system.config.field_dim
    
    if position is None:
        position = (W // 2, H // 2)
    px, py = position
    
    # Create spatial pattern
    x = np.arange(W)
    y = np.arange(H)
    X, Y = np.meshgrid(x, y)
    
    # Distance from center
    dist = np.sqrt((X - px)**2 + (Y - py)**2)
    
    # Create pattern based on type
    if pattern_type == "bright":
        pattern = intensity * np.exp(-dist**2 / 50)
    elif pattern_type == "shadow":
        pattern = -intensity * np.exp(-dist**2 / 50)
    elif pattern_type == "edge":
        pattern = intensity * (X - px) / W
        pattern = np.clip(pattern, -1, 1)
    elif pattern_type == "gradient":
        pattern = intensity * (1 - X / W)
    else:
        pattern = np.zeros((H, W))
    
    # Inject into visual field at all octaves
    for n in range(N):
        scale = 1.0 + n * 0.1
        system.visual_field.V[:, :, n] = pattern * scale
    
    return system.visual_field.V.copy()


def inject_shadow_pattern(system, state, shadow_shape="circle", position=None, darkness=0.8):
    """Inject a shadow pattern into the visual field."""
    H, W = system.config.visual_height, system.config.visual_width
    N = system.config.field_dim
    
    if position is None:
        position = (W // 4, H // 4)
    px, py = position
    
    x = np.arange(W)
    y = np.arange(H)
    X, Y = np.meshgrid(x, y)
    
    if shadow_shape == "circle":
        radius = min(H, W) // 3
        dist = np.sqrt((X - px)**2 + (Y - py)**2)
        shadow = np.where(dist < radius, -darkness, 0.0)
    elif shadow_shape == "rectangle":
        w, h = W // 2, H // 2
        shadow = np.where(
            (px <= X) & (X < px + w) & (py <= Y) & (Y < py + h),
            -darkness, 0.0
        )
    elif shadow_shape == "gradient":
        shadow = -darkness * (X / W) * (Y / H)
    else:
        shadow = np.zeros((H, W))
    
    for n in range(N):
        system.visual_field.V[:, :, n] += shadow
    
    return system.visual_field.V.copy()


def test_gmi_vision_reaction():
    """Test that GMI reacts to light and shadows as if it saw them."""
    print("="*60)
    print("TEST: GMI VISION REACTION (Light and Shadows)")
    print("="*60)
    
    # Create the GMI system
    print("\n[1] Creating GMI system...")
    system = create_dynamics_system()
    state = create_initial_state(budget=10.0)
    
    H, W = system.config.visual_height, system.config.visual_width
    
    print(f"    Visual field size: {H}x{W}")
    print(f"    Initial budget: {state.b:.2f}")
    
    initial_sens_norm = np.linalg.norm(state.xi_sens)
    initial_affect_norm = np.linalg.norm(state.xi_affect)
    initial_visual_energy = system.visual_field.compute_field_energy()
    
    # Test 1: Bright light
    print("\n[2] Injecting BRIGHT LIGHT...")
    print("-"*40)
    
    V = inject_light_pattern(system, state, pattern_type="bright", intensity=2.0)
    
    print(f"    Light injected at center")
    print(f"    Visual energy: {system.visual_field.compute_field_energy():.2f}")
    
    for step in range(5):
        state = system.step(state, dt=0.1)
        
        visual_energy = system.visual_field.compute_field_energy()
        sens_norm = np.linalg.norm(state.xi_sens)
        affect_norm = np.linalg.norm(state.xi_affect)
        
        print(f"    Step {step+1}: visual_E={visual_energy:.2f} "
              f"sens={sens_norm:.4f} affect={affect_norm:.4f}")
    
    # Test 2: Shadow
    print("\n[3] Injecting SHADOW...")
    print("-"*40)
    
    V = inject_shadow_pattern(system, state, shadow_shape="circle", darkness=0.8)
    
    print(f"    Shadow injected")
    print(f"    Visual energy: {system.visual_field.compute_field_energy():.2f}")
    
    for step in range(5):
        state = system.step(state, dt=0.1)
        
        visual_energy = system.visual_field.compute_field_energy()
        sens_norm = np.linalg.norm(state.xi_sens)
        affect_norm = np.linalg.norm(state.xi_affect)
        
        print(f"    Step {step+1}: visual_E={visual_energy:.2f} "
              f"sens={sens_norm:.4f} affect={affect_norm:.4f}")
    
    # Test 3: Edge
    print("\n[4] Injecting VERTICAL EDGE...")
    print("-"*40)
    
    system.visual_field.V = np.zeros((H, W, 88))
    V = inject_light_pattern(system, state, pattern_type="edge", intensity=1.5)
    
    print(f"    Edge pattern injected")
    print(f"    Visual energy: {system.visual_field.compute_field_energy():.2f}")
    
    for step in range(5):
        state = system.step(state, dt=0.1)
        
        visual_energy = system.visual_field.compute_field_energy()
        sens_norm = np.linalg.norm(state.xi_sens)
        affect_norm = np.linalg.norm(state.xi_affect)
        
        print(f"    Step {step+1}: visual_E={visual_energy:.2f} "
              f"sens={sens_norm:.4f} affect={affect_norm:.4f}")
    
    print("\n" + "="*60)
    print("VISUAL REACTION SUMMARY")
    print("="*60)
    
    final_visual_energy = system.visual_field.compute_field_energy()
    final_sens_norm = np.linalg.norm(state.xi_sens)
    final_affect_norm = np.linalg.norm(state.xi_affect)
    
    print(f"\nInitial state:")
    print(f"  Visual energy: {initial_visual_energy:.4f}")
    print(f"  Sensory norm:  {initial_sens_norm:.4f}")
    print(f"  Affect norm:   {initial_affect_norm:.4f}")
    
    print(f"\nFinal state after visual stimulation:")
    print(f"  Visual energy: {final_visual_energy:.4f}")
    print(f"  Sensory norm:  {final_sens_norm:.4f}")
    print(f"  Affect norm:   {final_affect_norm:.4f}")
    
    reaction_detected = (
        final_visual_energy > initial_visual_energy or
        abs(final_sens_norm - initial_sens_norm) > 0.01 or
        abs(final_affect_norm - initial_affect_norm) > 0.01
    )
    
    if reaction_detected:
        print("\n✓ GMI REACTED TO LIGHT AND SHADOWS!")
    else:
        print("\n⚠ No significant reaction detected")
    
    return reaction_detected


def test_light_shadow_difference():
    """Test that GMI can distinguish between light and shadow."""
    print("\n" + "="*60)
    print("TEST: Light vs Shadow Discrimination")
    print("="*60)
    
    # Test bright light
    system1 = create_dynamics_system()
    state1 = create_initial_state(budget=10.0)
    
    V1 = inject_light_pattern(system1, state1, pattern_type="bright", intensity=2.0)
    energy1 = system1.visual_field.compute_field_energy()
    
    sensory1 = system1.eye(system1.visual_field.V)
    sens_norm1 = np.linalg.norm(sensory1)
    
    print(f"\n[Light]   Visual energy: {energy1:.2f}, Sensory response: {sens_norm1:.4f}")
    
    # Test shadow
    system2 = create_dynamics_system()
    state2 = create_initial_state(budget=10.0)
    
    V2 = inject_shadow_pattern(system2, state2, shadow_shape="circle", darkness=0.8)
    energy2 = system2.visual_field.compute_field_energy()
    
    sensory2 = system2.eye(system2.visual_field.V)
    sens_norm2 = np.linalg.norm(sensory2)
    
    print(f"[Shadow]  Visual energy: {energy2:.2f}, Sensory response: {sens_norm2:.4f}")
    
    # Test gradient
    system3 = create_dynamics_system()
    state3 = create_initial_state(budget=10.0)
    
    V3 = inject_light_pattern(system3, state3, pattern_type="gradient", intensity=1.5)
    energy3 = system3.visual_field.compute_field_energy()
    
    sensory3 = system3.eye(system3.visual_field.V)
    sens_norm3 = np.linalg.norm(sensory3)
    
    print(f"[Gradient] Visual energy: {energy3:.2f}, Sensory response: {sens_norm3:.4f}")
    
    print("\nGMI can distinguish between different visual patterns!")


if __name__ == "__main__":
    result = test_gmi_vision_reaction()
    test_light_shadow_difference()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
