package es.primitiva.predictorwidget;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
public class MainActivity extends Activity {
 @Override public void onCreate(Bundle state){super.onCreate(state); WebView view=new WebView(this); view.setWebViewClient(new WebViewClient()); view.getSettings().setJavaScriptEnabled(true); setContentView(view); view.loadUrl("https://danielmigales.github.io/primitiva-IA/");}
}
