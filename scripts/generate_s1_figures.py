"""Generate S1 performance figures from the paper-profile technical output."""
import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/s1/generated_outputs'
data = json.loads((OUT/'s1_simulation_results.json').read_text())
rows = data['results']
fig, ax = plt.subplots(figsize=(9, 4.5))
bars = ax.barh([r['config_id'] for r in rows], [r['time_min'] for r in rows], color='#276B92')
ax.invert_yaxis()
for b, r in zip(bars, rows):
    ax.text(b.get_width()+0.3, b.get_y()+b.get_height()/2, f"{r['time_min']:.3f}", va='center')
ax.set(xlabel='Official MLPerf time-to-quality (minutes)', title='S1: observed ResNet-50 training time', xlim=(0, 30))
fig.tight_layout(); fig.savefig(OUT/'s1_training_time.png', dpi=220); plt.close(fig)
rows = data['deadline_sensitivity']
fig, ax = plt.subplots(figsize=(9, 4.5))
x = [r['deadline_min'] for r in rows]; y = [r['minimum_gpus'] for r in rows]
ax.step(x, y, where='post', color='#276B92'); ax.scatter(x, y, color='#276B92')
for r in rows:
    ax.annotate(r['minimum_gpu_config'], (r['deadline_min'], r['minimum_gpus']), xytext=(3, 6), textcoords='offset points', fontsize=8)
ax.set(xscale='log', xlabel='Required completion deadline (minutes)', ylabel='Recommended accelerators', title='S1: recommendation changes as the deadline tightens')
ax.set_xticks(x, [str(n) for n in x]); ax.set_yticks([4, 8, 16, 64]); ax.grid(alpha=.2)
fig.tight_layout(); fig.savefig(OUT/'s1_deadline_map.png', dpi=220); plt.close(fig)
print(OUT)
