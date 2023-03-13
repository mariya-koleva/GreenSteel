import numpy as np
import matplotlib.pyplot as plt

data_pressure_vessel = np.loadtxt("results_pressure_vessel/lcoh_vs_rating.txt")
data_salt_cavern = np.loadtxt("results_salt_cavern/lcoh_vs_rating.txt")
data_pipe = np.loadtxt("results_underground_pipe/lcoh_vs_rating.txt")

plt.plot(data_pressure_vessel[:,0]/800, data_pressure_vessel[:,1], label="Pressure Vessel")
plt.plot(data_pipe[:,0]/800, data_pipe[:,1], label="Underground Pipe")
plt.plot(data_salt_cavern[:,0]/800, data_salt_cavern[:,1], label="Salt Cavern")

plt.scatter(data_pressure_vessel[np.argmin(data_pressure_vessel[:,1]),0]/800, np.min(data_pressure_vessel[:,1]), color="k")
plt.scatter(data_pipe[np.argmin(data_pipe[:,1]),0]/800, np.min(data_pipe[:,1]), color="k")
plt.scatter(data_salt_cavern[np.argmin(data_salt_cavern[:,1]),0]/800, np.min(data_salt_cavern[:,1]), color="k")


# plt.xlim([0.2,1])
# plt.ylim([0,20])

plt.xlabel("Electrolyzer/Wind Plant Rating Ratio")
plt.ylabel("LCOH ($/kg)")
plt.legend(frameon=False)
plt.tight_layout()
plt.savefig("lcoh_vs_rating_ratio.pdf", transparent=True)
plt.show()