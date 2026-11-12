.class public final Lcom/easytech/ew5/modx$auto;
.super Ljava/lang/Thread;
.source "modx.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Thread;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    const/4 v0, 0x0

    :goto_loop
    const/16 v1, 0xa

    if-lt v0, v1, :modx_end

    const-wide/16 v2, 0xfa0

    :try_start_0
    invoke-static {v2, v3}, Ljava/lang/Thread;->sleep(J)V
    :try_end_0
    .catch Ljava/lang/InterruptedException; {:try_start_0 .. :try_end_0} :catch_0

    goto :modx_after

    :catch_0
    move-exception v4

    :modx_after
    invoke-static {}, Lcom/easytech/ew5/modx;->login()V

    add-int/lit8 v0, v0, 0x1

    goto :goto_loop

    :modx_end
    return-void
.end method
