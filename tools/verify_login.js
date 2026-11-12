Java.perform(function () {
  var A = Java.use("com.easytech.ew5.ew5Activity");
  A.nativeGameLoginSuccess.implementation = function (id, token) {
    console.log("[JAVA] nativeGameLoginSuccess(" + id + ")");
    return this.nativeGameLoginSuccess(id, token);
  };
  var R = Java.use("com.easytech.ew5.ew5Activity$32");
  R.run.implementation = function () {
    console.log("[JAVA] runnable32.run()");
    return this.run();
  };
  console.log("hooks ok");
  try { A.nativeGameLoginSuccess("direct_test", ""); console.log("direct call ok"); } catch (e) { console.log("direct err " + e); }
  try { A.getEw5Activity().wxSignIn(); console.log("wxSignIn ok"); } catch (e) { console.log("wx err " + e); }
});
