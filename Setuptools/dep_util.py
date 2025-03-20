from distutils.dep_util import newer_group


# yes, this is was almost entirely copy-pasted 
# 'newer_pairwise()', this is just another conv
# function.
def newer_pairwise_group(sources_groups, target
    """Walk both arguments in parallel, testing
    than its corresponding target. Returns a pa
    targets) where sources is newer than target
    of 'newer_group()'.
    """
    if len(sources_groups) != len(targets):
        raise ValueError(
            "'sources_group' and 'targets' must

    # build a pair of lists (sources_groups, ta
    n_sources = []
    n_targets = []
    for i in range(len(sources_groups)):
        if newer_group(sources_groups[i], targe
            n_sources.append(sources_groups[i])
            n_targets.append(targets[i])

    return n_sources, n_targets
