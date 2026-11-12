.class public final Lcom/easytech/ew5/modx;
.super Ljava/lang/Object;
.source "modx.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static buy()V
    .locals 1

    const/4 v0, 0x1

    invoke-static {v0}, Lcom/easytech/ew5/ew5Activity;->ResPurchase(I)V

    return-void
.end method

.method public static autoLogin()V
    .locals 1

    new-instance v0, Lcom/easytech/ew5/modx$auto;

    invoke-direct {v0}, Lcom/easytech/ew5/modx$auto;-><init>()V

    invoke-virtual {v0}, Lcom/easytech/ew5/modx$auto;->start()V

    return-void
.end method

.method public static login()V
    .locals 4

    sget-object v0, Lcom/easytech/ew5/ew5Activity;->mGLView:Lcom/easytech/ew5/ecGLSurfaceView;

    if-nez v0, :modx_done

    invoke-static {}, Lcom/easytech/ew5/ew5Activity;->getEw5Activity()Lcom/easytech/ew5/ew5Activity;

    move-result-object v1

    if-nez v1, :modx_done

    new-instance v2, Lcom/easytech/ew5/ew5Activity$32;

    const-string v3, "wxmod"

    invoke-direct {v2, v1, v3}, Lcom/easytech/ew5/ew5Activity$32;-><init>(Lcom/easytech/ew5/ew5Activity;Ljava/lang/String;)V

    invoke-virtual {v0, v2}, Lcom/easytech/ew5/ecGLSurfaceView;->queueEvent(Ljava/lang/Runnable;)V

    :modx_done
    return-void
.end method
