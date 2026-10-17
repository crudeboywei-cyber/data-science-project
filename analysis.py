"""Reproducible exploratory analysis of the public Palmer Penguins data.

Run from any directory: python analysis.py
Raw observations are never overwritten. No API key or internet is required.
"""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'penguins.csv'
OUT = ROOT
SPECIES = ['Adelie', 'Chinstrap', 'Gentoo']
COLORS = {'Adelie': '#185e83', 'Chinstrap': '#b05a28', 'Gentoo': '#087b65'}
SHAPES = {'Adelie': 'o', 'Chinstrap': '^', 'Gentoo': 's'}


def analyse(data):
    expected = {'species', 'island', 'bill_length_mm', 'bill_depth_mm',
                'flipper_length_mm', 'body_mass_g', 'sex', 'year'}
    if set(data.columns) != expected:
        raise ValueError('The source columns do not match the documented dataset.')
    if data['species'].isna().any() or not set(data['species']).issubset(SPECIES):
        raise ValueError('Missing or unexpected species labels need investigation.')
    mass = data.dropna(subset=['body_mass_g']).copy()
    pairs = data.dropna(subset=['flipper_length_mm', 'body_mass_g']).copy()
    if not (mass['body_mass_g'] > 0).all():
        raise ValueError('Non-positive mass requires source review.')
    if not (pairs['flipper_length_mm'] > 0).all():
        raise ValueError('Non-positive flipper length requires source review.')
    summary = mass.groupby('species')['body_mass_g'].agg(
        count='count', median_g='median', mean_g='mean',
        q1_g=lambda s: s.quantile(.25), q3_g=lambda s: s.quantile(.75)
    ).reindex(SPECIES)
    pooled_r = pairs['flipper_length_mm'].corr(pairs['body_mass_g'])
    within = {s: float(pairs.loc[pairs.species == s, 'flipper_length_mm'].corr(
        pairs.loc[pairs.species == s, 'body_mass_g'])) for s in SPECIES}
    metrics = {
        'source_rows': len(data), 'mass_rows': len(mass), 'pair_rows': len(pairs),
        'excluded_missing_mass': len(data)-len(mass),
        'excluded_missing_pairs': len(data)-len(pairs),
        'missing_per_column': {k: int(v) for k,v in data.isna().sum().items()},
        'species_summary': summary.reset_index().to_dict(orient='records'),
        'pooled_pearson_r': float(pooled_r), 'within_species_pearson_r': within,
        'observed_years': sorted(int(y) for y in data.year.unique()),
        'source_sha256': hashlib.sha256(DATA.read_bytes()).hexdigest(),
    }
    return mass, pairs, summary, metrics


def style(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color('#9caab2')
    ax.tick_params(colors='#334852')
    ax.grid(axis='y', color='#e2e8ec', linewidth=.8)
    ax.set_axisbelow(True)


def make_figures(mass, pairs, summary):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.labelcolor': '#203842', 'text.color': '#203842',
                         'svg.fonttype': 'none'})
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=160)
    values = [mass.loc[mass.species == s, 'body_mass_g'].to_numpy() for s in SPECIES]
    box = ax.boxplot(values, positions=[1,2,3], widths=.40, patch_artist=True,
                     showfliers=False, medianprops={'color':'#172b36', 'linewidth':2},
                     whiskerprops={'color':'#647780'}, capprops={'color':'#647780'})
    rng = np.random.default_rng(7204)
    for i, s in enumerate(SPECIES, 1):
        box['boxes'][i-1].set(facecolor=COLORS[s], alpha=.22, edgecolor=COLORS[s])
        ax.scatter(i+rng.uniform(-.12,.12,len(values[i-1])), values[i-1],
                   s=18, alpha=.42, color=COLORS[s], marker=SHAPES[s], linewidths=0)
        row = summary.loc[s]
        ax.text(i, 6600, f"n = {int(row['count'])}\nMedian = {row['median_g']:,.0f} g",
                ha='center', va='top', fontsize=11)
    ax.set_xticks([1,2,3], SPECIES)
    ax.set_ylabel('Body mass (g)')
    ax.set_xlabel('Penguin species')
    ax.set_ylim(2500, 6750)
    ax.set_title('Gentoo penguins have a higher median body mass in this sample',
                 loc='left', fontsize=15, pad=20, weight='medium')
    style(ax)
    fig.text(.10,.03, '342 observed masses. Points show individual penguins; boxes show the middle 50%.\n'
             'Two missing masses excluded. Palmer Archipelago, 2007–2009. Source: palmerpenguins (CC0).',
             fontsize=9, color='#526875')
    fig.subplots_adjust(left=.10,right=.97,top=.85,bottom=.20)
    fig.savefig(OUT/'body_mass_by_species.png', bbox_inches='tight')
    plt.close(fig)

    fig, axes = plt.subplots(1,3,figsize=(12,5.6),dpi=160,sharex=True,sharey=True)
    for ax, s in zip(axes, SPECIES):
        subset = pairs.loc[pairs.species == s]
        ax.scatter(subset.flipper_length_mm, subset.body_mass_g,
                   s=28, alpha=.65, color=COLORS[s], marker=SHAPES[s], linewidths=0)
        r = subset.flipper_length_mm.corr(subset.body_mass_g)
        ax.set_title(f'{s}\nn = {len(subset)}, Pearson r = {r:.2f}', fontsize=12, pad=12)
        ax.set_xlabel('Flipper length (mm)')
        ax.set_xlim(165,235)
        ax.set_ylim(2500,6500)
        style(ax)
    axes[0].set_ylabel('Body mass (g)')
    fig.suptitle('Longer flippers tend to accompany greater body mass within each species',
                 x=.08,ha='left',fontsize=15,weight='medium')
    fig.text(.08,.03,'Shared axes support fair comparison. 342 complete measurement pairs; two rows excluded.\n'
             'Correlation is descriptive, not evidence of causation. Source: palmerpenguins (CC0).',
             fontsize=9,color='#526875')
    fig.subplots_adjust(left=.08,right=.98,top=.76,bottom=.23,wspace=.14)
    fig.savefig(OUT/'flipper_mass_by_species.png',bbox_inches='tight')
    plt.close(fig)


def main():
    data = pd.read_csv(DATA)
    mass, pairs, summary, metrics = analyse(data)
    OUT.mkdir(exist_ok=True)
    summary.to_csv(OUT/'species_summary.csv')
    (OUT/'metrics.json').write_text(json.dumps(metrics, indent=2)+'\n',encoding='utf-8')
    make_figures(mass, pairs, summary)
    print(f"Source: {len(data)} rows; body-mass analysis: {len(mass)}; complete pairs: {len(pairs)}")
    print(summary.to_string())
    print('Pooled Pearson r:', round(metrics['pooled_pearson_r'],4))
    print('Within-species r:', metrics['within_species_pearson_r'])
    print('Saved two visualizations, summary table and metrics.json in the project root.')


if __name__ == '__main__':
    main()
