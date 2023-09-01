import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.patches as mpatches

import lab as B

from typing import Optional, Union, List, Tuple

from deepsensor.data.task import Task
from deepsensor.data.loader import TaskLoader
from deepsensor.data.processor import DataProcessor
from pandas import DataFrame


def context_encoding(
    model,
    task: Task,
    task_loader: TaskLoader,
    batch_idx: int = 0,
    context_set_idxs: Optional[Union[List[int], int]] = None,
    land_idx: Optional[int] = None,
    cbar: bool = True,
    clim: Optional[Tuple] = None,
    cmap: str = "viridis",
    verbose_titles: bool = True,
    titles: Optional[dict] = None,
    size: int = 3,
    return_axes: bool = False,
):
    """
    Plot the encoding of a context set in a task.

    Parameters
    ----------
    model : ...
        DeepSensor model
    task : deepsensor.data.task.Task
        Task containing context set to plot encoding of ...
    task_loader : deepsensor.data.loader.TaskLoader
        DataLoader used to load the data, containing context set metadata used
        for plotting.
    batch_idx : int, optional
        Batch index in encoding to plot, by default 0
    context_set_idxs : List[int] | int, optional
        Indices of context sets to plot, by default None (plots all context
        sets).
    land_idx : int, optional
        Index of the land mask in the encoding (used to overlay land contour
        on plots), by default None.
    cbar : bool, optional
        Whether to add a colorbar to the plots, by default True.
    clim : tuple, optional
        Colorbar limits, by default None.
    cmap : str, optional
        Color map to use for the plots, by default "viridis".
    verbose_titles : bool, optional
        Whether to include verbose titles for the variable IDs in the context
        set (including the time index), by default True.
    titles : list, optional
        List of titles to override for each subplot, by default None.
        If None, titles are generated from context set metadata.
    size : int, optional
        Size of the figure in inches, by default 3.
    return_axes : bool, optional
        Whether to return the axes of the figure, by default False.

    Returns
    -------
    matplotlib.pyplot.Figure | Tuple[matplotlib.pyplot.Figure, matplotlib.pyplot.Axes]
        Either a figure containing the context set encoding plots, or a tuple
        containing the figure and the axes of the figure (if ``return_axes``
        was set to ``True``).
    """
    from .model.nps import compute_encoding_tensor

    encoding_tensor = compute_encoding_tensor(model, task)
    encoding_tensor = encoding_tensor[batch_idx]

    if isinstance(context_set_idxs, int):
        context_set_idxs = [context_set_idxs]
    if context_set_idxs is None:
        context_set_idxs = np.array(range(len(task_loader.context_dims)))

    context_var_ID_set_sizes = [
        ndim + 1 for ndim in np.array(task_loader.context_dims)[context_set_idxs]
    ]  # Add density channel to each set size
    max_context_set_size = max(context_var_ID_set_sizes)
    ncols = max_context_set_size
    nrows = len(context_set_idxs)

    figsize = (ncols * size, nrows * size)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
    if nrows == 1:
        axes = axes[np.newaxis]

    channel_i = 0
    for ctx_i in context_set_idxs:
        if verbose_titles:
            var_IDs = task_loader.context_var_IDs_and_delta_t[ctx_i]
        else:
            var_IDs = task_loader.context_var_IDs[ctx_i]
        size = task_loader.context_dims[ctx_i] + 1  # Add density channel
        for var_i in range(size):
            ax = axes[ctx_i, var_i]
            # Need `origin="lower"` because encoding has `x1` increasing from
            # top to bottom, whereas in visualisations we want `x1` increasing
            # from bottom to top.
            im = ax.imshow(
                encoding_tensor[channel_i], origin="lower", clim=clim, cmap=cmap
            )
            if titles is not None:
                ax.set_title(titles[channel_i])
            elif var_i == 0:
                ax.set_title(f"Density {ctx_i}")
            elif var_i > 0:
                ax.set_title(f"{var_IDs[var_i - 1]}")
            if var_i == 0:
                ax.set_ylabel(f"Context set {ctx_i}")
            if cbar:
                divider = make_axes_locatable(ax)
                cax = divider.append_axes("right", size="5%", pad=0.05)
                plt.colorbar(im, cax)
            ax.patch.set_edgecolor("black")
            ax.patch.set_linewidth(1)
            if land_idx is not None:
                ax.contour(
                    encoding_tensor[land_idx], colors="k", levels=[0.5], origin="lower"
                )
            ax.tick_params(
                which="both",
                bottom=False,
                left=False,
                labelbottom=False,
                labelleft=False,
            )
            channel_i += 1
        for var_i in range(size, ncols):
            # Hide unused axes
            ax = axes[ctx_i, var_i]
            ax.axis("off")

    plt.tight_layout()
    if not return_axes:
        return fig
    elif return_axes:
        return fig, axes


def offgrid_context(
    axes: Union[np.ndarray, List[plt.Axes], Tuple[plt.Axes]],
    task: Task,
    data_processor: Optional[DataProcessor] = None,
    task_loader: Optional[TaskLoader] = None,
    plot_target: bool = False,
    add_legend: bool = True,
    context_set_idxs: Optional[Union[List[int], int]] = None,
    markers: Optional[str] = None,
    colors: Optional[str] = None,
    **scatter_kwargs,
) -> None:
    """
    Plot the off-grid context points on ``axes``.

    Uses ``data_processor`` to unnormalise the context coordinates if provided.

    Parameters
    ----------
    axes : numpy.ndarray | List[matplotlib.pyplot.Axes] | Tuple[matplotlib.pyplot.Axes
        ...
    task : deepsensor.data.task.Task
        ...
    data_processor : deepsensor.data.processor.DataProcessor, optional
        ..., by default None.
    task_loader : deepsensor.data.loader.TaskLoader, optional
        ..., by default None.
    plot_target : bool, optional
        ..., by default False.
    add_legend : bool, optional
        ..., by default True.
    context_set_idxs : List[int] | int, optional
        ..., by default None.
    markers : str, optional
        ..., by default None.
    colors : str, optional
        ..., by default None.
    scatter_kwargs : dict, optional
        ..., by default {}.

    Returns
    -------
    None.
    """
    if markers is None:
        markers = "ovs^D"
    if colors is None:
        colors = "kbrgy"

    if isinstance(context_set_idxs, int):
        context_set_idxs = [context_set_idxs]

    if type(axes) is np.ndarray:
        axes = axes.ravel()
    elif not isinstance(axes, (list, tuple)):
        axes = [axes]

    if plot_target:
        X = [*task["X_c"], *task["X_t"]]
    else:
        X = task["X_c"]

    for set_i, X in enumerate(X):
        if context_set_idxs is not None and set_i not in context_set_idxs:
            continue

        if isinstance(X, tuple):
            continue  # Don't plot gridded context data locations
        if X.ndim == 3:
            X = X[0]  # select first batch

        if data_processor is not None:
            x1, x2 = data_processor.map_x1_and_x2(X[0], X[1], unnorm=True)
            X = np.stack([x1, x2], axis=0)

        X = X[::-1]  # flip 2D coords for Cartesian fmt

        label = ""
        if plot_target and set_i < len(task["X_c"]):
            label += f"Context set {set_i} "
            if task_loader is not None:
                label += f"({task_loader.context_var_IDs[set_i]})"
        elif plot_target and set_i >= len(task["X_c"]):
            label += f"Target set {set_i - len(task['X_c'])} "
            if task_loader is not None:
                label += f"({task_loader.target_var_IDs[set_i - len(task['X_c'])]})"

        for ax in axes:
            ax.scatter(
                *X,
                marker=markers[set_i],
                color=colors[set_i],
                **scatter_kwargs,
                facecolors=None if markers[set_i] == "x" else "none",
                label=label,
            )

    if add_legend:
        axes[0].legend(loc="best")


def offgrid_context_observations(
    axes: Union[np.ndarray, List[plt.Axes], Tuple[plt.Axes]],
    task: Task,
    data_processor: DataProcessor,
    task_loader: TaskLoader,
    context_set_idx: int,
    format_str: Optional[str] = None,
    extent: Optional[Tuple[int, int, int, int]] = None,
    color: str = "black",
) -> None:
    """
    Plot unnormalised context observation values.

    Parameters
    ----------
    axes: numpy.ndarray | List[matplotlib.pyplot.Axes] | Tuple[matplotlib.pyplot.Axes
        ...
    task: deepsensor.data.task.Task
        ...
    data_processor: deepsensor.data.processor.DataProcessor
        ...
    task_loader: deepsensor.data.loader.TaskLoader
        ...
    context_set_idx: int
        ...
    format_str: str, optional
        ..., by default None.
    extent: Tuple[int, int, int, int], optional
        ..., by default None.
    color: str, optional
        ..., by default "black".

    Returns
    -------
    None.
    """
    if type(axes) is np.ndarray:
        axes = axes.ravel()
    elif not isinstance(axes, (list, tuple)):
        axes = [axes]

    if format_str is None:
        format_str = ""

    var_ID = task_loader.context_var_IDs[
        context_set_idx
    ]  # Tuple of variable IDs for the context set
    assert (
        len(var_ID) == 1
    ), "Plotting context observations only supported for single-variable (1D) context sets"
    var_ID = var_ID[0]

    X_c = task["X_c"][context_set_idx]
    assert not isinstance(
        X_c, tuple
    ), f"The context set must not be gridded but is of type {type(X_c)} for context set at index {context_set_idx}"
    X_c = data_processor.map_coord_array(X_c, unnorm=True)

    Y_c = task["Y_c"][context_set_idx]
    assert Y_c.ndim == 2
    assert Y_c.shape[0] == 1
    Y_c = data_processor.map_array(Y_c, var_ID, unnorm=True).ravel()

    for x_c, y_c in zip(X_c.T, Y_c):
        if extent is not None:
            if not (
                extent[0] <= x_c[0] <= extent[1] and extent[2] <= x_c[1] <= extent[3]
            ):
                continue
        for ax in axes:
            ax.text(*x_c[::-1], format_str.format(float(y_c)), color=color)


def receptive_field(
    receptive_field, data_processor: DataProcessor, crs, extent: str = "global"
) -> plt.Figure:
    """
    ...

    Parameters
    ----------
    receptive_field : ...
        ...
    data_processor : deepsensor.data.processor.DataProcessor
        ...
    crs : ...
        ...
    extent : str, optional
        ..., by default "global".

    Returns
    -------
    None.
    """
    fig, ax = plt.subplots(subplot_kw=dict(projection=crs))

    if extent == "global":
        ax.set_global()
    else:
        ax.set_extent(extent, crs=crs)

    x11, x12 = data_processor.norm_params["coords"]["x1"]["map"]
    x21, x22 = data_processor.norm_params["coords"]["x2"]["map"]

    x1_rf_raw = receptive_field * (x12 - x11)
    x2_rf_raw = receptive_field * (x22 - x21)

    x1_midpoint_raw = (x12 + x11) / 2
    x2_midpoint_raw = (x22 + x21) / 2

    # Compute bottom left corner of receptive field
    x1_corner = x1_midpoint_raw - x1_rf_raw / 2
    x2_corner = x2_midpoint_raw - x2_rf_raw / 2

    ax.add_patch(
        mpatches.Rectangle(
            xy=[x2_corner, x1_corner],  # Cartesian fmt: x2, x1
            width=x2_rf_raw,
            height=x1_rf_raw,
            facecolor="black",
            alpha=0.3,
            transform=crs,
        )
    )
    ax.coastlines()
    ax.gridlines(draw_labels=True, alpha=0.2)

    x1_name = data_processor.norm_params["coords"]["x1"]["name"]
    x2_name = data_processor.norm_params["coords"]["x2"]["name"]
    ax.set_title(
        f"Receptive field in raw coords: {x1_name}={x1_rf_raw:.2f}, "
        f"{x2_name}={x2_rf_raw:.2f}"
    )

    return fig


def feature_maps(
    model,
    task: Task,
    n_features_per_layer: int = 1,
    seed: Optional[int] = None,
    figsize: int = 3,
    add_colorbar: bool = False,
    cmap: str = "Greys",
) -> plt.Figure:
    """
    Plot the feature maps of a ``ConvNP`` model's decoder layers after a
    forward pass with a ``Task``.

    Currently only plots feature maps for the downsampling path.

    ..
        TODO: Work out how to construct partial U-Net including the upsample
        path.

    Parameters
    ----------
    model : ...
        ...
    task : deepsensor.data.task.Task
        ...
    n_features_per_layer : int, optional
        ..., by default 1.
    seed : int, optional
        ..., by default None.
    figsize : int, optional
        ..., by default 3.
    add_colorbar : bool, optional
        ..., by default False.
    cmap : str, optional
        ..., by default "Greys".

    Returns
    -------
    matplotlib.pyplot.Figure
        A figure containing the feature maps.

    Raises
    ------
    ValueError
        If the backend is not recognised.
    """
    from .model.nps import compute_encoding_tensor

    import deepsensor

    # Hacky way to load the correct __init__.py to get `convert_to_tensor` method
    if deepsensor.backend.str == "tf":
        import deepsensor.tensorflow as deepsensor
    elif deepsensor.backend.str == "torch":
        import deepsensor.torch as deepsensor
    else:
        raise ValueError(f"Unknown backend: {deepsensor.backend.str}")

    unet = model.model.decoder[0]

    # Produce encoding
    x = deepsensor.convert_to_tensor(compute_encoding_tensor(model, task))

    # Manually construct the U-Net forward pass from
    # `neuralprocesses.construct_convgnp` to get the feature maps
    def unet_forward(unet, x):
        feature_maps = []

        h = unet.activations[0](unet.before_turn_layers[0](x))
        hs = [h]
        feature_map = B.to_numpy(h)
        feature_maps.append(feature_map)
        for layer, activation in zip(
            unet.before_turn_layers[1:],
            unet.activations[1:],
        ):
            h = activation(layer(hs[-1]))
            hs.append(h)
            feature_map = B.to_numpy(h)
            feature_maps.append(feature_map)

        # Now make the turn!

        h = unet.activations[-1](unet.after_turn_layers[-1](hs[-1]))
        feature_map = B.to_numpy(h)
        feature_maps.append(feature_map)
        for h_prev, layer, activation in zip(
            reversed(hs[:-1]),
            reversed(unet.after_turn_layers[:-1]),
            reversed(unet.activations[:-1]),
        ):
            h = activation(layer(B.concat(h_prev, h, axis=1)))
            feature_map = B.to_numpy(h)
            feature_maps.append(feature_map)

        h = unet.final_linear(h)
        feature_map = B.to_numpy(h)
        feature_maps.append(feature_map)

        return feature_maps

    feature_maps = unet_forward(unet, x)

    figs = []
    rng = np.random.default_rng(seed)
    for layer_i, feature_map in enumerate(feature_maps):
        n_features = feature_map.shape[1]
        n_features_to_plot = min(n_features_per_layer, n_features)
        feature_idxs = rng.choice(n_features, n_features_to_plot, replace=False)

        fig, axes = plt.subplots(
            nrows=1,
            ncols=n_features_to_plot,
            figsize=(figsize * n_features_to_plot, figsize),
        )
        if n_features_to_plot == 1:
            axes = [axes]
        for f_i, ax in zip(feature_idxs, axes):
            fm = feature_map[0, f_i]
            im = ax.imshow(fm, origin="lower", cmap=cmap)
            ax.set_title(f"Feature {f_i}", fontsize=figsize * 15 / 4)
            ax.tick_params(
                which="both",
                bottom=False,
                left=False,
                labelbottom=False,
                labelleft=False,
            )
            if add_colorbar:
                cbar = ax.figure.colorbar(im, ax=ax, format="%.2f")

        fig.suptitle(
            f"Layer {layer_i} feature map. Shape: {feature_map.shape}. Min={np.min(feature_map):.2f}, Max={np.max(feature_map):.2f}.",
            fontsize=figsize * 15 / 4,
        )
        plt.tight_layout()
        plt.subplots_adjust(top=0.75)
        figs.append(fig)

    return figs


def placements(
    task: Task,
    X_new_df: DataFrame,
    data_processor: DataProcessor,
    crs,
    extent: Optional[Union[Tuple[int, int, int, int], str]] = None,
    figsize: int = 3,
    **scatter_kwargs,
) -> plt.Figure:
    """
    ...

    Parameters
    ----------
    task : deepsensor.data.task.Task
        ...
    X_new_df : pandas.DataFrame
        ...
    data_processor : deepsensor.data.processor.DataProcessor
        ...
    crs : ...
        ...
    extent : Tuple[int, int, int, int] | str, optional
        ..., by default None.
    figsize : int, optional
        ..., by default 3.

    Returns
    -------
    matplotlib.pyplot.Figure
        A figure containing the placement plots.
    """
    fig, ax = plt.subplots(subplot_kw={"projection": crs}, figsize=(figsize, figsize))
    ax.scatter(*X_new_df.values.T[::-1], c="r", linewidths=0.5, **scatter_kwargs)
    offgrid_context(ax, task, data_processor, linewidths=0.5, **scatter_kwargs)

    ax.coastlines()
    if extent is None:
        pass
    elif extent == "global":
        ax.set_global()
    else:
        ax.set_extent(extent, crs=crs)

    return fig


def acquisition_fn(
    task: Task,
    acquisition_fn_ds,
    X_new_df: DataFrame,
    data_processor: DataProcessor,
    crs,
    col_dim: str = "iteration",
    cmap: str = "Greys_r",
    figsize: int = 3,
    add_colorbar: bool = True,
    max_ncol: int = 5,
) -> plt.Figure:
    """
    ...

    Parameters
    ----------
    task : deepsensor.data.task.Task
        ...
    acquisition_fn_ds : ...
        ...
    X_new_df : pandas.DataFrame
        ...
    data_processor : deepsensor.data.processor.DataProcessor
        ...
    crs : ...
        ...
    col_dim : str, optional
        ..., by default "iteration".
    cmap : str, optional
        ..., by default "Greys_r".
    figsize : int, optional
        ..., by default 3.
    add_colorbar : bool, optional
        ..., by default True.
    max_ncol : int, optional
        ..., by default 5.

    Returns
    -------
    matplotlib.pyplot.Figure
        A figure containing the acquisition function plots.

    Raises
    ------
    ValueError
        If a column dimension is encountered that is not one of
        ``["time", "sample"]``.
    """
    # Remove spatial dims using data_processor.raw_spatial_coords_names
    plot_dims = [col_dim, *data_processor.raw_spatial_coord_names]
    non_plot_dims = [dim for dim in acquisition_fn_ds.dims if dim not in plot_dims]
    valid_avg_dims = ["time", "sample"]
    for dim in non_plot_dims:
        if dim not in valid_avg_dims:
            raise ValueError(
                f"Cannot average over dim {dim} for plotting. Must be one of {valid_avg_dims}. "
                f"Select a single value for {dim} using `acquisition_fn_ds.sel({dim}=...)`."
            )
    if len(non_plot_dims) > 0:
        # Average over non-plot dims
        print(f"Averaging acquisition function over dims for plotting: {non_plot_dims}")
        acquisition_fn_ds = acquisition_fn_ds.mean(dim=non_plot_dims)

    col_vals = acquisition_fn_ds[col_dim].values
    if col_vals.size == 1:
        n_col_vals = 1
    else:
        n_col_vals = len(col_vals)
    ncols = np.min([max_ncol, n_col_vals])

    if n_col_vals > ncols:
        nrows = int(np.ceil(n_col_vals / ncols))
    else:
        nrows = 1

    fig, axes = plt.subplots(
        subplot_kw={"projection": crs},
        ncols=ncols,
        nrows=nrows,
        figsize=(figsize * ncols, figsize * nrows),
    )
    if nrows == 1 and ncols == 1:
        axes = [axes]
    else:
        axes = axes.ravel()
    if add_colorbar:
        min, max = acquisition_fn_ds.min(), acquisition_fn_ds.max()
    else:
        # Use different colour scales for each plot
        min, max = None, None
    for i, col_val in enumerate(col_vals):
        ax = axes[i]
        if i == len(col_vals) - 1:
            final_axis = True
        else:
            final_axis = False
        acquisition_fn_ds.sel(**{col_dim: col_val}).plot(
            ax=ax, cmap=cmap, vmin=min, vmax=max, add_colorbar=False
        )
        if add_colorbar and final_axis:
            im = ax.get_children()[0]
            label = acquisition_fn_ds.name
            cax = plt.axes([0.93, 0.035, 0.02, 0.91])  # add a small custom axis
            cbar = plt.colorbar(
                im, cax=cax, label=label
            )  # specify axis for colorbar to occupy with cax
        ax.set_title(f"{col_dim}={col_val}")
        ax.coastlines()
        if col_dim == "iteration":
            X_new_df_plot = X_new_df.loc[slice(0, col_val)].values.T[::-1]
        else:
            # Assumed plotting single iteration
            iter = acquisition_fn_ds.iteration.values
            assert iter.size == 1, "Expected single iteration"
            X_new_df_plot = X_new_df.loc[slice(0, iter.item())].values.T[::-1]
        ax.scatter(
            *X_new_df_plot,
            c="r",
            linewidths=0.5,
        )

    offgrid_context(axes, task, data_processor, linewidths=0.5)

    # Remove any unused axes
    for ax in axes[len(col_vals) :]:
        ax.remove()

    return fig
