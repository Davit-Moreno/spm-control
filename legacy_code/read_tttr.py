import tttrlib
import matplotlib.pyplot as plt

# Load the TTTR file
file_path = "C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2024-12-20\tttr_scanpq22"  # Replace with your actual file path
data = tttrlib.TTTR(file_path)

# Extract photon arrival times and channel numbers
arrival_times = data.time
channels = data.channel

# Visualize photon arrival times
plt.figure(figsize=(10, 5))
plt.plot(arrival_times[:1000], label="Photon Arrival Times")  # Plot first 1000 events
plt.xlabel("Event Index")
plt.ylabel("Time (ps)")
plt.title("Photon Arrival Times")
plt.legend()
plt.show()

# Count events per channel
unique_channels, counts = np.unique(channels, return_counts=True)
plt.bar(unique_channels, counts)
plt.xlabel("Channel Number")
plt.ylabel("Event Count")
plt.title("Channel Event Distribution")
plt.show()
