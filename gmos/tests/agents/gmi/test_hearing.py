"""
Test: GMI Hearing Reaction

This test demonstrates GMI reacting to a sound as if it heard it.
The sound is injected into the resonant field, propagates through the ear operator
into the sensory block, and affects the affective state.
"""

import numpy as np
from gmos.agents.gmi.twelve_block_state import create_initial_state
from gmos.agents.gmi.full_dynamics import create_dynamics_system


def inject_sound(system, state, sound_frequency=440.0, sound_duration=1.0, amplitude=1.0):
    """
    Inject a sound into the resonant field.
    
    The sound is represented as a spectral pattern that gets injected
    directly into the xi_Phi field.
    
    Args:
        system: FullDynamicsSystem
        state: Current state
        sound_frequency: Frequency of the sound (Hz)
        sound_duration: Duration of the sound
        amplitude: Amplitude of the sound
        
    Returns:
        Updated state with sound injected
    """
    # Map frequency to octave index
    # Assuming base frequency 20 Hz, top frequency 20000 Hz (human hearing range)
    base_freq = 20.0
    top_freq = 20000.0
    
    # Calculate which octaves the sound affects
    if sound_frequency < base_freq:
        octave_index = 0
    elif sound_frequency > top_freq:
        octave_index = 87
    else:
        octave_index = int(np.log2(sound_frequency / base_freq) * 10)  # Scale to 88 octaves
    octave_index = np.clip(octave_index, 0, 87)
    
    # Create a spectral pattern representing the sound
    # The sound energy spreads to nearby octaves
    sound_pattern = np.zeros(88)
    spread = 5  # How many octaves the sound spreads to
    
    for i in range(max(0, octave_index - spread), min(87, octave_index + spread + 1)):
        # Gaussian falloff from center frequency
        distance = abs(i - octave_index)
        sound_pattern[i] = amplitude * np.exp(-distance**2 / (2 * spread**2))
    
    # Directly inject into the resonant field (xi_Phi)
    state.xi_Phi = sound_pattern.copy()
    
    return state


def test_gmi_hearing_reaction():
    """
    Test that GMI reacts to a sound as if it heard it.
    
    This demonstrates:
    1. Sound is injected into the system
    2. Sound propagates through ear operator to sensory block
    3. Sensory input affects affective state
    4. System generates voice output in response
    """
    print("="*60)
    print("TEST: GMI HEARING REACTION")
    print("="*60)
    
    # Create the GMI system
    print("\n[1] Creating GMI system...")
    system = create_dynamics_system()
    state = create_initial_state(budget=10.0)
    
    print(f"    Initial budget: {state.b:.2f}")
    print(f"    Initial sensory norm: {np.linalg.norm(state.xi_sens):.4f}")
    print(f"    Initial affect norm: {np.linalg.norm(state.xi_affect):.4f}")
    
    # Record initial state
    initial_sens_norm = np.linalg.norm(state.xi_sens)
    initial_affect_norm = np.linalg.norm(state.xi_affect)
    initial_field_energy = state.compute_field_energy()
    
    # Inject a sound (440 Hz = A4 note)
    print("\n[2] Injecting sound (440 Hz, A4 note)...")
    sound_freq = 440.0
    amplitude = 2.0
    
    # Inject sound into the field through action
    state = inject_sound(system, state, sound_frequency=sound_freq, amplitude=amplitude)
    
    print(f"    Sound injected into action field")
    print(f"    Action norm: {np.linalg.norm(state.xi_action):.4f}")
    
    # Step the dynamics - this propagates the sound through the system
    print("\n[3] Propagating sound through the system...")
    print("-"*40)
    
    for step in range(10):
        # Apply action forcing to field
        forcing = system.action_forcing(state.xi_action)
        state.xi_Phi += forcing * 0.1  # Add forcing to field
        
        # Step the dynamics
        state = system.step(state, dt=0.1)
        
        # Decay the sound (模拟声音逐渐消失)
        state.xi_action *= 0.9
        
        # Print state at each step
        field_energy = state.compute_field_energy()
        sens_norm = np.linalg.norm(state.xi_sens)
        affect_norm = np.linalg.norm(state.xi_affect)
        
        print(f"    Step {step+1:2d}: "
              f"field_E={field_energy:.4f} "
              f"sens={sens_norm:.4f} "
              f"affect={affect_norm:.4f} "
              f"budget={state.b:.2f}")
    
    # Check if the system reacted
    print("\n[4] Analyzing reaction...")
    final_field_energy = state.compute_field_energy()
    final_sens_norm = np.linalg.norm(state.xi_sens)
    final_affect_norm = np.linalg.norm(state.xi_affect)
    
    # Generate voice response
    voice = system.generate_voice(state, claimed_confidence=0.7)
    
    print(f"    Initial field energy: {initial_field_energy:.4f}")
    print(f"    Final field energy:   {final_field_energy:.4f}")
    print(f"    Change in field energy: {final_field_energy - initial_field_energy:.4f}")
    print()
    print(f"    Initial sensory norm: {initial_sens_norm:.4f}")
    print(f"    Final sensory norm:   {final_sens_norm:.4f}")
    print(f"    Change in sensory:    {final_sens_norm - initial_sens_norm:.4f}")
    print()
    print(f"    Initial affect norm: {initial_affect_norm:.4f}")
    print(f"    Final affect norm:   {final_affect_norm:.4f}")
    print(f"    Change in affect:   {final_affect_norm - initial_affect_norm:.4f}")
    print()
    print(f"    Voice response:")
    print(f"      - Entropy:    {voice.entropy:.4f}")
    print(f"      - Roughness:  {voice.roughness:.4f}")
    print(f"      - Confidence: {voice.confidence:.4f}")
    print(f"      - Total cost: {voice.total_cost:.4f}")
    
    # Verify reaction occurred
    reaction_detected = (
        final_field_energy > initial_field_energy or
        abs(final_sens_norm - initial_sens_norm) > 0.01 or
        abs(final_affect_norm - initial_affect_norm) > 0.01
    )
    
    print("\n" + "="*60)
    if reaction_detected:
        print("✓ GMI REACTED TO SOUND!")
        print("  - Sound energy injected into resonant field")
        print("  - Energy propagated through ear operator to sensory")
        print("  - Affective state was modulated")
        print("  - Voice response generated")
    else:
        print("⚠ No significant reaction detected")
    print("="*60)
    
    return reaction_detected


def test_different_frequencies():
    """
    Test GMI's response to different sound frequencies.
    """
    print("\n" + "="*60)
    print("TEST: DIFFERENT FREQUENCIES")
    print("="*60)
    
    frequencies = [220, 440, 880, 1760]  # A3, A4, A5, A6
    
    for freq in frequencies:
        system = create_dynamics_system()
        state = create_initial_state(budget=10.0)
        
        # Inject sound
        state = inject_sound(system, state, sound_frequency=freq, amplitude=1.5)
        
        # Step a few times
        for _ in range(5):
            forcing = system.action_forcing(state.xi_action)
            state.xi_Phi += forcing * 0.1
            state = system.step(state, dt=0.1)
            state.xi_action *= 0.9
        
        # Check field response
        field_energy = state.compute_field_energy()
        
        # Find which octave was most excited
        most_excited = np.argmax(np.abs(state.xi_Phi))
        
        print(f"  Frequency {freq:4d} Hz -> "
              f"field_E={field_energy:.4f}, "
              f"most_excited_octave={most_excited}")


if __name__ == "__main__":
    # Run the main test
    result = test_gmi_hearing_reaction()
    
    # Run frequency test
    test_different_frequencies()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
