
"""
Created on Mon Dec  3 15:45:48 2018

@author: Murat Cem Köse
"""

def _FineTuneByN(sc_data,refDataset,annot,de,scores,n):
    """ Applies fine tuning and return final annotations of single cells.

    Parameters
    ----------
    sc_data : DataFrame
        Sc-RNAseq data.
        
    refDataset : DataFrame
        The reference dataset gene expression matrix.
        
    annot : DataFrame
        Annotations for each column in ref_data.
        
    de : Dict
        Differentially expressed genes for each combination of cell types.
        
    scores : DataFrame
        Correlation scores from the first round.
        
    n : Int
        The number of top cell types to choose for the first fine tuning.
        
    Returns
    -------
    final_annotations : DataFrame
        A data frame with the final annotations of cell types for each single cell.
        
    """
    d={}
    [d.update({i:np.sort(scores.sort_index(by=i,ascending=False).index.values[0:n])}) for i in scores.columns]
    while(n>1):
        unique_types=[list(x) for x in set(tuple(x) for x in d.values())]
        for i in unique_types:
            cols=[j for j in d.keys() if list(d.get(j))==i]
            top_labels=i
            res=_FineTuneRoundByN(sc_data,refDataset,annot,top_labels,de,cols)
            [d.update({cols[t]:res[t]}) for t in range(len(cols))]
        n=n-1
    return pd.DataFrame(d,index=["final_annotations"])

def _FineTuneRoundByN(sc_data,refDataset,annot,top_labels,de,cols):
    """ Returns final annotations of single cells.

    Parameters
    ----------
    sc_data : DataFrame
        Sc-RNAseq data.
        
    refDataset : DataFrame
        The reference dataset gene expression matrix.
        
    annot : DataFrame
        Annotations for each column in ref_data.
        
    top_labels: List
        Most correlated cell types from the previous round.
        
    de : Dict
        Differentially expressed genes for each combination of cell types.
        
    cols : List
        Cell names to calculate correlations.
        
    Returns
    -------
    top_annotations : List
        A list of cell types that are associated with given cells.
        
    """
    refDataset=refDataset.T
    refDataset["cell_types"]=annot["cellType"].get_values()
    refDataset=refDataset[refDataset["cell_types"].isin(top_labels)]
    del refDataset["cell_types"]
    refDataset=refDataset.T
    annot=annot[annot["cellType"].isin(top_labels)]
    n=int(500*np.power(2/3,np.log2(len(np.unique(annot.cellType)))))
    de=getDEgenes(refDataset,annot=annot,n=n)
    de_merged=[]
    [de_merged.extend(i) for i in  de.values()]
    de_merged=np.unique(de_merged)

    cor=scipy.stats.spearmanr(sc_data.loc[de_merged,cols],refDataset.loc[de_merged])
    cor=pd.DataFrame(cor[0]).iloc[:,0:len(cols)][-len(refDataset.columns):]
    cor.columns=cols
    cor.index=refDataset.columns
    cor["cellType"]=annot["cellType"].values
    scores=cor.groupby("cellType").quantile(q=0.8)
    return [scores.sort_index(by=i,ascending=False).index.values[0:len(top_labels)-1] for i in scores.columns]

def _FineTuneByT(sc_data,refDataset,annot,de,scores,threshold):
    """ Applies fine tuning and return final annotations of single cells.

    Parameters
    ----------
    sc_data : DataFrame
        Sc-RNAseq data.
        
    refDataset : DataFrame
        The reference dataset gene expression matrix.
        
    annot : DataFrame
        Annotations for each column in ref_data.
        
    de : Dict
        Differentially expressed genes for each combination of cell types.
        
    scores : DataFrame
        Correlation scores from the first round.
        
    threshold : Float
        The cutoff value for correlation scores of cell types to choose for the first fine tuning.
        
    Returns
    -------
    final_annotations : DataFrame
        A data frame with the final annotations of cell types for each single cell.
        
    """
    final_annotations=pd.DataFrame(index=["annotation"])
    for i in sc_data.columns:
        top_labels=scores[scores[i]>0.05].index.values
        while(len(top_labels)>1):
            top_labels=_FineTuneRoundByT(sc_data,refDataset,annot,top_labels,de,i)
        final_annotations[i]=top_labels[0]
    return final_annotations

def _FineTuneRoundByT(sc_data,refDataset,annot,top_labels,de,i):
    """ Returns final annotations of single cells.

    Parameters
    ----------
    sc_data : DataFrame
        Sc-RNAseq data.
        
    refDataset : DataFrame
        The reference dataset gene expression matrix.
        
    annot : DataFrame
        Annotations for each column in ref_data.
        
    top_labels: List
        Most correlated cell types from the previous round.
        
    de : Dict
        Differentially expressed genes for each combination of cell types.
        
    i : String
        The cell name to calculate correlations for.
        
    Returns
    -------
    top_annotations : List
        A list of cell types that are associated with given cells.
        
    """
    refDataset=refDataset.T
    refDataset["cell_types"]=annot["cellType"].get_values()
    refDataset=refDataset[refDataset["cell_types"].isin(top_labels)]
    del refDataset["cell_types"]
    refDataset=refDataset.T
    annot=annot[annot["cellType"].isin(top_labels)]

    n=int(500*np.power(2/3,np.log2(len(np.unique(annot.cellType)))))
    de=getDEgenes(refDataset,annot=annot,n=n)
    de_merged=[]
    [de_merged.extend(j) for j in  de.values()]
    de_merged=np.unique(de_merged)

    cor=scipy.stats.spearmanr(sc_data.loc[de_merged,i],refDataset.loc[de_merged])
    cor=pd.DataFrame(cor[0]).iloc[:,0:1][-len(refDataset.columns):]
    cor.columns=[i]
    cor.index=refDataset.columns
    cor["cellType"]=annot["cellType"].values
    scores=cor.groupby("cellType").quantile(q=0.8)
    scores=scores.sort_values(by=i,ascending=False)
    scores=scores.drop(scores.index[-1])
    return scores.index