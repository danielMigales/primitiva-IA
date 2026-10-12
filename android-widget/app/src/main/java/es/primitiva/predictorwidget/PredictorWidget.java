package es.primitiva.predictorwidget;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
public class PredictorWidget extends AppWidgetProvider {
 static final String DATA="https://danielmigales.github.io/primitiva-IA/data/reto-predictor.json";
 @Override public void onUpdate(Context context,AppWidgetManager manager,int[] ids){for(int id:ids)render(context,manager,id,"Cargando combinación…","Consultando GitHub"); new Thread(()->{String numbers="Sin predicción",date="Consulta la aplicación";try{HttpURLConnection c=(HttpURLConnection)new URL(DATA).openConnection();c.setConnectTimeout(10000);c.setReadTimeout(10000);try(InputStream in=c.getInputStream()){JSONObject root=new JSONObject(new String(in.readAllBytes(),StandardCharsets.UTF_8));JSONArray arr=root.getJSONArray("predictions");if(arr.length()>0){JSONObject last=arr.getJSONObject(arr.length()-1);JSONArray ns=last.getJSONArray("nums");StringBuilder b=new StringBuilder();for(int i=0;i<ns.length();i++){if(i>0)b.append(" · ");b.append(ns.getInt(i));}numbers=b.toString();date="Sorteo: "+last.getString("target")+" · Objetivo: 3 aciertos";}}finally{c.disconnect();}}catch(Exception e){date="Sin conexión · toca para abrir";}final String n=numbers,d=date;for(int id:ids)render(context,manager,id,n,d);}).start();}
 static void render(Context context,AppWidgetManager manager,int id,String nums,String date){RemoteViews v=new RemoteViews(context.getPackageName(),R.layout.widget);v.setTextViewText(R.id.numbers,nums);v.setTextViewText(R.id.date,date);Intent intent=new Intent(context,MainActivity.class);PendingIntent p=PendingIntent.getActivity(context,0,intent,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);v.setOnClickPendingIntent(R.id.numbers,p);v.setOnClickPendingIntent(R.id.title,p);v.setOnClickPendingIntent(R.id.date,p);manager.updateAppWidget(id,v);}
}
