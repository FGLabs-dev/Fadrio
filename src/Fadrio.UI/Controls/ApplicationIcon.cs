using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Fadrio.Core;
using Fadrio.Infrastructure;

namespace Fadrio.UI.Controls;

/// <summary>Loads only validated local icons, without blocking the dispatcher.</summary>
public sealed class ApplicationIcon : UserControl
{
    public static readonly StyledProperty<IconReference?> ReferenceProperty =
        AvaloniaProperty.Register<ApplicationIcon, IconReference?>(nameof(Reference));
    public static readonly StyledProperty<string> FallbackProperty =
        AvaloniaProperty.Register<ApplicationIcon, string>(nameof(Fallback), "?");

    private static readonly LocalIconResolver Resolver = new();
    // Bound simultaneous icon-tree searches and decodes across all rows.
    private static readonly SemaphoreSlim LoadGate = new(2);
    private readonly Image _image = new() { Stretch = Stretch.Uniform };
    private readonly TextBlock _fallback = new()
    {
        FontSize = 16,
        HorizontalAlignment = Avalonia.Layout.HorizontalAlignment.Center,
        VerticalAlignment = Avalonia.Layout.VerticalAlignment.Center
    };
    private CancellationTokenSource? _request;
    private Bitmap? _bitmap;
    private bool _attached;

    public ApplicationIcon()
    {
        IsHitTestVisible = false;
        Content = new Grid { Children = { _fallback, _image } };
    }

    public IconReference? Reference
    {
        get => GetValue(ReferenceProperty);
        set => SetValue(ReferenceProperty, value);
    }

    public string Fallback
    {
        get => GetValue(FallbackProperty);
        set => SetValue(FallbackProperty, value);
    }

    protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
    {
        base.OnPropertyChanged(change);
        if (change.Property == FallbackProperty) _fallback.Text = Fallback;
        if (change.Property == ReferenceProperty && _attached) Reload();
    }

    protected override void OnAttachedToVisualTree(VisualTreeAttachmentEventArgs e)
    {
        base.OnAttachedToVisualTree(e);
        _attached = true;
        _fallback.Text = Fallback;
        Reload();
    }

    protected override void OnDetachedFromVisualTree(VisualTreeAttachmentEventArgs e)
    {
        _attached = false;
        Clear();
        base.OnDetachedFromVisualTree(e);
    }

    private void Clear()
    {
        _request?.Cancel();
        _request = null;
        _image.Source = null;
        _bitmap?.Dispose();
        _bitmap = null;
        _fallback.IsVisible = true;
    }

    private async void Reload()
    {
        Clear();
        if (Reference is not { } reference) return;
        using var request = new CancellationTokenSource();
        _request = request;
        Bitmap? loaded = null;
        try
        {
            loaded = await Task.Run(async () =>
            {
                await LoadGate.WaitAsync(request.Token).ConfigureAwait(false);
                try
                {
                    var resolved = await Resolver.ResolveAsync(reference, request.Token).ConfigureAwait(false);
                    if (resolved is null) return null;
                    request.Token.ThrowIfCancellationRequested();
                    using FileStream stream = File.OpenRead(resolved.Path);
                    // Bound both dimensions, including extremely tall or wide PNGs.
                    try
                    {
                        return resolved.Width >= resolved.Height
                            ? Bitmap.DecodeToWidth(stream, 64)
                            : Bitmap.DecodeToHeight(stream, 64);
                    }
                    catch (NullReferenceException)
                    {
                        // Avalonia.Skia 12.1.2 dereferences a null codec for a
                        // header-only PNG. Contain that decoder failure here.
                        return null;
                    }
                }
                finally { LoadGate.Release(); }
            }, request.Token);
            if (request.IsCancellationRequested || !_attached || !ReferenceEquals(_request, request)) return;
            _bitmap = loaded;
            loaded = null;
            _image.Source = _bitmap;
            _fallback.IsVisible = _bitmap is null;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException
            or ArgumentException or InvalidOperationException or NotSupportedException or OperationCanceledException)
        {
            // Missing, changing, or undecodable artwork is a normal fallback condition.
        }
        finally
        {
            loaded?.Dispose();
            if (ReferenceEquals(_request, request)) _request = null;
        }
    }
}
