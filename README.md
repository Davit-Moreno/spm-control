spm-control

Control and acquisition software for a custom single-particle fluorescence microscope (SPM) in the Alivisatos Group at the University of Chicago. The microscope is used to study photoluminescence blinking in individual colloidal quantum dots.

The app replaces a set of separate scripts and vendor tools with one GUI. It handles stage control, raster scanning, live photon counts and time-tagged photon acquisition, and it is in regular use in the lab.

<!-- Add a screenshot of the GUI here, e.g. ![SPM App](docs/screenshot.png) -->
What it does
Raster scanning: drives a 3-axis piezo nanopositioning stage across a sample, records photon counts at each point and builds a live intensity map for locating single emitters.
Live count display: streams real-time count rates from both single-photon avalanche diode (SPAD) channels.
Point selection: pick a bright spot on a finished scan and move the stage to it for single-particle measurements.
Time-tagged photon acquisition (TTTR): runs T2/T3 time-tagged measurements on a PicoQuant HydraHarp 400 and saves the raw photon records for analysis.
TTTR decoding: parses raw T2 records (bitmask decoding of timing, channel and overflow fields) into photon arrival times for blinking and photon-correlation (g²) analysis.
File explorer: browse and reopen saved scans and measurements from inside the app.
Config-driven: hardware settings (stage, detector sync/CFD levels) and scan parameters live in YAML files in config_files/, separate from the code.
Hardware
Component	Model	Interface
Piezo stage + controller	Physik Instrumente P-517.3CD + E-727	pipython
Time-correlated single-photon counter	PicoQuant HydraHarp 400	vendor DLL via ctypes
Detectors	2× SPADs (Hanbury Brown–Twiss configuration)	via HydraHarp

Hardware access goes through abstract interfaces (spm_control/hardware/interfaces.py), so new stages or detectors can be added without changing the GUI.

Project layout
spm_control/
  gui/          # customtkinter app: main window, mode pages (scan, TTTR, explorer, ML), live displays
  managers/     # threaded controllers for hardware, raster scans, TTTR runs, counts and timing
  hardware/     # stage and detector drivers behind common interfaces
  scan/         # raster path generation, focusing, scan plotting
  analysis/     # TTTR record decoding, I/O, plotting
  legacy_scripts/  # original standalone scripts the app replaced (kept for reference)
config_files/   # hardware.yaml, scan.yaml
tests/
Installation

Requires Python 3.10+. Driving the hardware requires Windows with the PicoQuant HydraHarp driver installed.

bash
git clone https://github.com/Davit-Moreno/spm-control.git
cd spm-control
pip install -e ".[hardware,tttr]"     # or ".[all]" for analysis/detection extras
Usage
Edit config_files/hardware.yaml for your stage and detector settings, and config_files/scan.yaml for scan range, resolution and the data folder.
Launch the app:
bash
python -m spm_control.gui.app
Use Scan to raster a region, select a bright spot, then use TTTR to record time-tagged photon data from that particle.
Roadmap

Ongoing work (2026–27) to make the microscope run unattended:

Automatic detection of single emitters in raster scans (neural network compared against a Ricker-wavelet baseline)
Autofocus with the fine (piezo) stage
Motorized detector balancing and filter control
Motorized coarse stage for moving between sample regions, with safe movement limits
A fully automated scan → detect → measure loop
Acknowledgments

Developed by Davit Moreno in the Alivisatos Group, University of Chicago. Builds on earlier lab scripts (legacy_scripts/) written by previous group members.
