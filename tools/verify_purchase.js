Java.perform(function () {
  var A = Java.use("com.easytech.ew5.ew5Activity");
  A.PurchaseSuccess.implementation = function (code, order) {
    console.log("[JAVA] PurchaseSuccess(" + code + ", " + order + ")");
    return this.PurchaseSuccess(code, order);
  };
  A.ResPurchase.implementation = function (code) {
    console.log("[JAVA] ResPurchase(" + code + ")");
    return this.ResPurchase(code);
  };
  console.log("hooks ok");
  try {
    var act = A.getEw5Activity();
    console.log("activity=" + act);
    act.StartPurchase("MODTEST_ORDER_1", 3, 2);
    console.log("StartPurchase invoked");
  } catch (e) { console.log("err " + e); }
});
