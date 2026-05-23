---
name: forge2d flipper torque
description: forge2d revolute joint motor torque must account for flipper moment of inertia; 1200 was way too low
type: feedback
originSessionId: 07eae58d-fd29-4ed7-967b-976c8786246a
---
With flipper density=100, l=9, t=1.6, I_pivot ≈ 39,000 kg·cm². For a 45ms stroke (52°), required torque ≈ 35 million. `flipperTorque = 1200` caused ~7-second stroke time — visually indistinguishable from not working.

**Why:** Box2D/forge2d maxMotorTorque limits what the motor can apply. If torque < I × α_needed, the joint moves so slowly it looks broken.

**How to apply:** When tuning revolute joint motors, compute I_pivot = mass × l² / 3 (thin rod about end), then T_needed = I × (2 × stroke / t²). With high-density flippers, torque will be in the millions.
