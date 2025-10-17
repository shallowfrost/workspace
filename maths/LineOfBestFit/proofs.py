import numpy as np
import matplotlib.pyplot as plt
import time

pointsCount = 10000
pltRange = 100
sepRange = 20
dotSize = 4
lineWidth = 2
length = pltRange

angle = np.random.uniform(0, 2 * np.pi)
center_x = np.random.uniform(0, pltRange)
center_y = np.random.uniform(0, pltRange)

t = np.linspace(-length / 2, length / 2, pointsCount)
raw_x = center_x + t * np.cos(angle) + np.random.normal(0, pltRange / sepRange, pointsCount)
raw_y = center_y + t * np.sin(angle) + np.random.normal(0, pltRange / sepRange, pointsCount)

x = np.clip(raw_x, 0, pltRange)
y = np.clip(raw_y, 0, pltRange)

mask = (x == raw_x) & (y == raw_y)
minim = min(len(x), len(y)) - 1

x = (x[mask])[:minim]
y = (y[mask])[:minim]

# =============================
start = time.time()
rise = []; run = []
count = 0
for i,_ in enumerate(x):
    for j in range(i + 1, len(x)):
        rise.append(y[i]-y[j])
        run.append(x[i]-x[j])
        count += 1

ax = np.average(x); ay = np.average(y)
slope = np.average(sum(rise)/sum(run))
b = ay - slope*ax

plotx = np.array([0, pltRange])
ploty = slope * plotx + b

print(count, len(x), time.time()-start)
print(f"Line of best fit: y = {slope:.4f}x + {b:.4f}")
# =============================

plt.scatter(x, y, color='blue', s=dotSize, label='Data points')
plt.plot(plotx, ploty, color='red', linewidth=lineWidth, label='Line of best fit')
plt.xlim(0, pltRange); plt.ylim(0, pltRange)
plt.xlabel('X-axis'); plt.ylabel('Y-axis')
plt.legend(); plt.show()