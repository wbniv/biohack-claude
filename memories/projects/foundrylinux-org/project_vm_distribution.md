---
name: project_vm_distribution
description: "VM downloads (VirtualBox OVA, VMware VMDK, QEMU qcow2) are a planned distribution channel, not placeholders"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2fd1d1ef-55cc-4978-8ec8-c8f0dd66d5a7
---

The VM download rows in the install section of foundrylinux.org are a deliberate distribution strategy — pre-built VM images for VirtualBox, VMware, and QEMU. They are not placeholders to be replaced.

**Why:** Will confirmed this explicitly when I incorrectly replaced them with the ISO block.

**How to apply:** When updating the download section, add new formats *alongside* the VM rows, never remove them. The `href="#"` links are intentional stubs until the images are built.
