import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def load_data(file_path):
    # Load the data from the CSV file
    data = pd.read_csv(file_path, header=None, names=['channel_1', 'channel_2', 'left_pulse', 'right_pulse', 'left_time_bin', 'right_time_bin', 'correlation_counts'])
    return data

def separate_correlations(data):
    # Separate auto-correlation (where channel_1 == channel_2) and cross-correlation (where channel_1 != channel_2)
    auto_correlation = data[data['channel_1'] == data['channel_2']]
    cross_correlation = data[data['channel_1'] != data['channel_2']]
    return auto_correlation, cross_correlation


def sep_pulses(correlation): 
        left=correlation[correlation['left_pulse']==-1.5]
        center=correlation[correlation['left_pulse']==-0.5]
        right=correlation[correlation['right_pulse']==1.5]
        return left, center, right


def plot_correlation(left, center,right, repetition_rate,value, label):
    # Calculate time shifts
    time_shift = 10**12 / repetition_rate
    
    # Adjust the time bins
    adjusted_left_time_bin = (left['left_time_bin'] - time_shift)/1000
    adjusted_right_time_bin = (right['left_time_bin'] + time_shift)/1000
    
    plt.figure(figsize=(6, 6))
    plt.plot(adjusted_left_time_bin, left['correlation_counts'], 'o',color='grey', alpha=0.3,label='Side Pulse')
    plt.plot(adjusted_right_time_bin, right['correlation_counts'],'o',color='grey', alpha=0.3, label='')
    
    # Plot the center pulse at time 0
    plt.plot(center['left_time_bin']/1000, center['correlation_counts'],'o', color='black', label='Center Pulse')
    plt.annotate(r'$g^{(2)}(0) = $ %.2f'%value, (-500, 5.5),size=22)
    plt.xlabel('Time (ns)',size=26)
    plt.ylabel('Correlation Counts',size=26)
    plt.tick_params(axis='both', labelsize=22)
    #plt.legend(fontsize=22,markerscale=3)
    plt.tight_layout()
    plt.show()

def main(file_path, repetition_rate):
    data = load_data(file_path)
    auto_correlation, cross_correlation = separate_correlations(data)
    left,center,right=sep_pulses(cross_correlation)
    aleft,acenter,aright=sep_pulses(auto_correlation)
    left_int=np.sum(left['correlation_counts'])
    right_int=np.sum(right['correlation_counts'])
    center_int=2*np.sum(center['correlation_counts'])
    g20=(center_int/(left_int + right_int))
    print(center_int/(left_int + right_int))

    plot_correlation(left,center,right, repetition_rate,g20, "Cross-correlation")


if __name__ == "__main__":
    file_path = r"C:\Users\spmno\OneDrive\Documents\spm\Scan\Scan Data\2026-10-05\Scan3_X55.4Y29.2Z10_CW_1.95uW_10min.ptu.g2.run\g2"
    # Replace with your actual file path. should be the actual g2 file inside the run folder. ########
    repetition_rate = 10**6  # Replace with your actual laser repetition rate (in Hz) ########
    main(file_path, repetition_rate)
