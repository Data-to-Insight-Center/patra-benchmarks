import pandas as pd
import matplotlib.pyplot as plt

client = pd.read_csv('/home/exouser/client/mcp/benchmark_results/run_2025_10_26/native/get_modelcard.csv')
server = pd.read_csv('/home/exouser/client/mcp/benchmark_results/run_2025_10_26/native/get_modelcard_db.csv', header=None, names=['total_time'])

rtt = client['response_time_ms']
db = server['total_time']

# y axis should start from 0, the gap between the axis and db should be filled with a color and the gap between db and rtt should be filled with a color
# plt.figure(figsize=(10, 5))
# plt.fill_between(rtt.index, db, color='green', alpha=0.3, label='DB Overhead')
# plt.fill_between(db.index, rtt, db, color='red', alpha=0.3, label='MCP Overhead')
# plt.ylabel('Time (ms)')
# plt.xlabel('Run')
# plt.title('Native MCP')
# plt.grid(True, alpha=0.3)
# plt.legend(loc='upper right')
# plt.tight_layout()
# plt.savefig('native_mcp.png')

# plot a stacked bar chart showing the mean of db and rtt
db_mean = db.mean()
rtt_mean = rtt.mean()
mcp_mean = rtt_mean - db_mean
plt.figure(figsize=(5, 3))
plt.bar(['MCP'], [db_mean], color='green', label='DB Overhead')
plt.bar(['MCP'], [mcp_mean], color='red', bottom=db_mean, label='MCP Overhead')
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig('native_mcp.png')