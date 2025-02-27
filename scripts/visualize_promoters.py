"""
This script creates visualizations for comparing promoter activity between BG and BM samples.

Key features:
- Creates MA plots showing fold changes vs mean expression
- Generates peak intensity distribution plots
- Shows chromosome-wise distribution of changes
- Calculates and outputs summary statistics
- Handles empty data cases with appropriate warnings
- Saves all plots and statistics to sample-specific directories

Input:
- Tab-separated comparison file with promoter data
- Output directory for plots and statistics
- Sample name for identification

Output:
- MA plot showing differential promoter activity
- Peak intensity distribution plots
- Chromosome-wise change distribution plots
- Summary statistics and significant changes files
- Detailed logging information
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

# Configure logging to show informational messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def visualize_promoters(comparison_file, output_dir, sample_name):
    """
    Create visualizations for promoter comparison between BG and BM samples.
    
    Args:
        comparison_file (str): Path to tab-separated comparison data file
        output_dir (str): Directory to save visualization outputs
        sample_name (str): Name identifier for the sample
        
    Returns:
        dict: Summary statistics of the comparison
    """
    
    # Create sample-specific output directory for organization
    sample_output_dir = os.path.join(output_dir, sample_name)
    os.makedirs(sample_output_dir, exist_ok=True)
    
    # Read the comparison data
    df = pd.read_csv(comparison_file, sep='\t')
    logger.info(f"Loaded {len(df)} promoters from comparison file")
    
    # Handle case where no data is found
    if len(df) == 0:
        logger.warning("No data found in comparison file. Skipping visualizations.")
        return {
            'Total promoters': 0,
            'Mean BG intensity': 0,
            'Mean BM intensity': 0,
            'Promoters up in BM (FC > 2)': 0,
            'Promoters down in BM (FC < -2)': 0,
            'Median fold change': 0,
            'Mean fold change': 0,
            'Std fold change': 0
        }

    # Configure plot style settings
    plt.style.use('default')
    sns.set_theme(style="whitegrid")
    
    # Create MA Plot showing relationship between mean counts and fold changes
    plt.figure(figsize=(12, 8))
    mean_counts = (df['bg_mean'] + df['bm_mean']) / 2
    
    # Color-code points based on fold change thresholds
    colors = ['red' if x < -1 else 'blue' if x > 1 else 'gray' for x in df['log2_fold_change']]
    plt.scatter(np.log2(mean_counts + 1), df['log2_fold_change'], 
               alpha=0.6, c=colors, s=50)
    
    # Process significant peaks for labeling
    significant_peaks = df[abs(df['log2_fold_change']) > 1].copy()
    significant_peaks['abs_fc'] = abs(significant_peaks['log2_fold_change']).astype(float)
    
    # Identify top changed peaks in each direction
    try:
        top_up = significant_peaks[significant_peaks['log2_fold_change'] > 0].nlargest(10, 'abs_fc')
        top_down = significant_peaks[significant_peaks['log2_fold_change'] < 0].nlargest(10, 'abs_fc')
    except (TypeError, ValueError) as e:
        logger.warning(f"Could not determine top peaks due to data type issue: {str(e)}")
        top_up = pd.DataFrame()
        top_down = pd.DataFrame()
    
    # Helper function to add gene labels to plot
    def add_labels(peaks, color):
        for _, peak in peaks.iterrows():
            x = np.log2(((peak['bg_mean'] + peak['bm_mean'])/2) + 1)
            y = peak['log2_fold_change']
            label = peak['gene']
            
            plt.annotate(label, 
                        xy=(x, y), 
                        xytext=(5, 5), 
                        textcoords='offset points',
                        fontsize=8,
                        color=color,
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color=color, alpha=0.5))
    
    # Add labels for top changing genes
    add_labels(top_up, 'blue')
    add_labels(top_down, 'red')
    
    # Add reference lines
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    plt.axhline(y=1, color='blue', linestyle='--', alpha=0.3)
    plt.axhline(y=-1, color='red', linestyle='--', alpha=0.3)
    
    plt.xlabel('log2 Mean Count')
    plt.ylabel('log2 Fold Change (BM/BG)')
    plt.title('MA Plot: Mean vs Fold Change')
    
    # Add summary statistics to plot
    up_regulated = (df['log2_fold_change'] > 1).sum()
    down_regulated = (df['log2_fold_change'] < -1).sum()
    plt.text(0.02, 0.98, 
            f'Up in BM (FC > 2): {up_regulated}\nDown in BM (FC < -2): {down_regulated}', 
            transform=plt.gca().transAxes, 
            verticalalignment='top',
            bbox=dict(facecolor='white', alpha=0.8))
    
    # Add plot legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                  label='Up in BM', markersize=8),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                  label='Down in BM', markersize=8),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', 
                  label='No change', markersize=8)
    ]
    plt.legend(handles=legend_elements, loc='lower right')
    
    plt.savefig(os.path.join(sample_output_dir, f'ma_plot_{sample_name}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create distribution plots
    plt.figure(figsize=(15, 6))
    
    # Plot peak intensity distributions
    plt.subplot(1, 2, 1)
    sns.kdeplot(data=np.log2(df['bg_mean'] + 1), label='BG', color='blue', fill=True, alpha=0.3)
    sns.kdeplot(data=np.log2(df['bm_mean'] + 1), label='BM', color='red', fill=True, alpha=0.3)
    plt.xlabel('log2(Peak Intensity + 1)')
    plt.ylabel('Density')
    plt.title('Distribution of Peak Intensities')
    plt.legend()
    
    # Plot fold change distribution
    plt.subplot(1, 2, 2)
    sns.histplot(data=df, x='log2_fold_change', bins=50, color='purple', alpha=0.6)
    plt.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    plt.axvline(x=1, color='blue', linestyle='--', alpha=0.3)
    plt.axvline(x=-1, color='red', linestyle='--', alpha=0.3)
    plt.xlabel('log2 Fold Change (BM/BG)')
    plt.ylabel('Count')
    plt.title('Distribution of Fold Changes')
    
    plt.tight_layout()
    plt.savefig(os.path.join(sample_output_dir, f'intensity_distributions_{sample_name}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create chromosome-wise distribution plots
    plt.figure(figsize=(15, 8))
    chr_changes = df.groupby('chr')['log2_fold_change'].agg(['mean', 'count', 'std']).reset_index()
    
    # Sort chromosomes naturally (1,2,3...X,Y)
    chr_changes['chr_num'] = chr_changes['chr'].str.extract('(\d+|X|Y)').fillna('Z')
    chr_changes = chr_changes.sort_values('chr_num')
    
    # Plot mean fold changes by chromosome
    plt.subplot(1, 2, 1)
    bars = plt.bar(range(len(chr_changes)), chr_changes['mean'], 
                  yerr=chr_changes['std'], capsize=5)
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    plt.xticks(range(len(chr_changes)), chr_changes['chr'], rotation=45)
    plt.xlabel('Chromosome')
    plt.ylabel('Mean log2 Fold Change ± SD')
    plt.title('Mean Fold Change by Chromosome')
    
    # Add value labels to bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=8)
    
    # Plot promoter counts by chromosome
    plt.subplot(1, 2, 2)
    bars = plt.bar(range(len(chr_changes)), chr_changes['count'])
    plt.xticks(range(len(chr_changes)), chr_changes['chr'], rotation=45)
    plt.xlabel('Chromosome')
    plt.ylabel('Number of Promoters')
    plt.title('Promoter Count by Chromosome')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom',
                fontsize=8)
    
    plt.tight_layout()
    plt.savefig(os.path.join(sample_output_dir, f'chromosome_distribution_{sample_name}.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Calculate summary statistics
    summary = {
        'Total promoters': len(df),
        'Mean BG intensity': df['bg_mean'].mean(),
        'Mean BM intensity': df['bm_mean'].mean(),
        'Promoters up in BM (FC > 2)': (df['log2_fold_change'] > 1).sum(),
        'Promoters down in BM (FC < -2)': (df['log2_fold_change'] < -1).sum(),
        'Median fold change': df['log2_fold_change'].median(),
        'Mean fold change': df['log2_fold_change'].mean(),
        'Std fold change': df['log2_fold_change'].std()
    }
    
    # Save summary statistics to file
    with open(os.path.join(sample_output_dir, f'summary_statistics_{sample_name}.txt'), 'w') as f:
        for key, value in summary.items():
            f.write(f"{key}: {value:.2f}\n")
    
    # Save significantly changed promoters
    significant_promoters = df[abs(df['log2_fold_change']) > 1].sort_values('log2_fold_change', ascending=False)
    significant_promoters.to_csv(os.path.join(sample_output_dir, f'significant_changes_{sample_name}.tsv'), sep='\t', index=False)
    
    logger.info("Visualization completed successfully")
    return summary

def main():
    """Parse command line arguments and run visualization pipeline."""
    parser = argparse.ArgumentParser(description='Visualize promoter comparison results')
    parser.add_argument('--input', required=True,
                        help='Promoter comparison file')
    parser.add_argument('--output-dir', required=True,
                        help='Output directory for plots')
    parser.add_argument('--sample-name', required=True,
                        help='Sample name')
    
    args = parser.parse_args()
    
    try:
        summary = visualize_promoters(args.input, args.output_dir, args.sample_name)
        for key, value in summary.items():
            logger.info(f"{key}: {value:.2f}")
    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()

"""
Summary of Code Functionality:

This script provides comprehensive visualization and analysis of promoter activity 
differences between BG (background) and BM (treatment) samples. It generates:

1. MA Plots:
   - Shows relationship between mean expression and fold changes
   - Highlights significantly changed promoters
   - Labels top changing genes

2. Distribution Plots:
   - Peak intensity distributions for both conditions
   - Fold change distribution across all promoters

3. Chromosome Analysis:
   - Mean fold changes by chromosome
   - Promoter count distribution across chromosomes

4. Statistical Summaries:
   - Calculates key metrics like total promoters, mean intensities
   - Identifies significantly up/down regulated promoters
   - Outputs detailed statistics to files

The code handles error cases, provides detailed logging, and organizes outputs
in a sample-specific directory structure. It's designed for analyzing differential
promoter activity in genomic data, particularly useful for ChIP-seq or similar
experiments comparing two conditions.
"""