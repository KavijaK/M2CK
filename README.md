# Two-Way Digital Paging System using SDRs
### EN2130: Communication Design Project | University of Moratuwa
**Department of Computer Science & Engineering**

---

## 📌 Project Overview
This repository contains the implementation of a functional two-way digital paging system developed using **Software Defined Radios (SDRs)**. The system is designed to facilitate reliable text communication between two nodes, incorporating custom addressing, error detection, and a feedback-based acknowledgment (ACK) mechanism.

The project focuses on the practical application of digital communication theory, specifically focusing on framing, synchronization, and hardware-software co-design.

## 🏗 System Architecture

### 📡 Physical Layer (PHY)
* **Modulation:** **QPSK** (Quadrature Phase Shift Keying) for optimized spectral efficiency (2 bits/symbol).
* **Pulse Shaping:** Root Raised Cosine (RRC) filter with a roll-off factor of $\alpha = 0.35$.
* **Hardware:** BladeRF x40/x115 SDR platforms.
* **Synchronization:** Costas Loop for carrier recovery and Mueller & Müller for symbol timing recovery.

### 🛠 Data Link Layer (DLL)
* **Framing:** Custom packet structure including Preamble and Sync Words for frame alignment.
* **Addressing:** Unique 8-bit IDs for each node to ensure point-to-point delivery.
* **Error Detection:** **CRC-16** validation on every received packet to ensure data integrity.
* **ACK Protocol:** A "Stop-and-Wait" mechanism where the receiver sends a confirmation packet back to the sender upon successful CRC validation.

## 📦 Repository Structure
```text
├── gnu-radio/          # GNU Radio (.grc) files for simulation and hardware
├── gui-app/                 # Python source code for UI and protocol logic        
├── video/                # Video
└── README.md            # Project documentation
