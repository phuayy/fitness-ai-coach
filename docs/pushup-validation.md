# Push-Up Side-Profile Validation

The first validator uses simple geometry over MediaPipe landmarks.

## Side Selection

The validator compares visible left-side landmarks and right-side landmarks, then selects the side with stronger average visibility.

## Main Metrics

- Elbow angle: shoulder-elbow-wrist
- Body line angle: shoulder-hip-ankle
- Upper arm to torso angle: elbow-shoulder-hip
- Forearm verticality score: horizontal drift between elbow and wrist
- Neck angle: ear-shoulder-hip

## Stage Detection

- Top: elbow angle >= 155 degrees
- Bottom: elbow angle <= 95 degrees
- Moving: between 95 and 155 degrees

## Rep Counting Rule

A repetition counts only when the user goes:

```text
top -> bottom with valid form -> top
```

If the bottom position is invalid, returning to top does not increment the count.
