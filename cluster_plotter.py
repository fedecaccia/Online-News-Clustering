import time
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import datetime
import settings

# import plotly.plotly as py
# import plotly.graph_objs as go

class ClusterPlotter(object):

	"""Matplotlib plotter plots bubble clusters"""

	def __init__(self):
		pass

	def update_annot(self, ind):
		index = ind["ind"][0]
		pos = self.sc.get_offsets()[index]
		self.annot.xy = pos
		text = self.names[index]
		self.annot.set_text(text)
		self.annot.set_bbox(dict(facecolor='blue', alpha=0.15))
		self.annot.set_family("sans-serif")
		self.annot.set_color("black")

	def hover(self, event):
		vis = self.annot.get_visible()
		if event.inaxes == self.ax:
			cont, ind = self.sc.contains(event)
			if cont:
				self.update_annot(ind)
				self.annot.set_visible(True)
				self.fig.canvas.draw_idle()
			else:
				if vis:
					self.annot.set_visible(False)
					self.fig.canvas.draw_idle()

	def plot(self, x, y, sizes, text, plot_at):

		self.x = np.array(x)
		self.y = np.array(y)
		self.z = np.array(sizes)
		self.names = np.array(text)

		self.fig = plt.figure(3, figsize=(10,8), facecolor="white", edgecolor="black")
		self.ax = plt.gca()
		plt.subplots_adjust(left=0.15, bottom=0.13)
		plt.title("Crypto bursting items at "+str(plot_at),
					fontdict={"fontsize":14, "fontweight":2}, weight="bold", 
					fontname='Sans', color = "black")
		plt.xlabel('Creation time [UTC]', size=12, fontname='Sans', color = "black")
		plt.ylabel('Last activity [UTC]', size=12, fontname='Sans', color = "black")        
		plt.xticks(rotation=30, size=12, color="black")
		plt.yticks(size=12, color="black")
		self.ax.set_facecolor("white")

		xmax = max(x)
		xmin = min(x)
		deltax = (xmax-xmin)/10
		plt.xlim(left=xmin-deltax, right=xmax+deltax)

		ymax = max(y)
		ymin = min(y)
		deltay = (ymax-ymin)/10        
		plt.ylim(bottom=ymin-deltay, top=ymax+deltay)

		# hfmt = matplotlib.dates.DateFormatter('%H:%M:%S')
		hfmt = matplotlib.dates.DateFormatter('%d-%m %H:%M')
		self.ax.xaxis.set_major_formatter(hfmt)
		self.ax.yaxis.set_major_formatter(hfmt)

		# s regulates size, c regulate color
		self.sc = plt.scatter(self.x, self.y, s=self.z*10, c=self.z, 
								cmap="Blues", alpha=0.4, edgecolors="grey", linewidths=2)

		self.annot = plt.annotate('text',
					xycoords='data', xy=(3, 1),
					textcoords='axes fraction', xytext=(0.1, 0.2),
					bbox=dict(boxstyle="round", fc="w"),
					arrowprops=dict(facecolor='black', arrowstyle='fancy'))
		self.annot.set_visible(False)
		self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

		plt.show()


# class ClusterPlotlyPlotter(object):

#     """plotly plotter plots bubble clusters"""

#     def __init__(self):
#         pass

#     def plot(self, x, y, sizes, text, plot_at):
#         sizes = np.array(sizes)
#         trace = go.Scatter(
#             x=x,
#             y=y,
#             text=text,
#             mode='markers',
#             marker=dict(
#                 opacity='size',
#                 size=sizes,
#                 sizemode='area',
#                 sizeref=2.*max(sizes)/(30.**2),
#                 sizemin=4,
#                 color = 'rgba(0, 0, 152, .8)',
#                 line = dict(
#                     width = 1,
#                     color = 'rgb(0, 0, 0, .2)'
#                 )
#             )
#         )

#         layout = go.Layout(
#             title='Crypto bursting items at '+str(plot_at),
#             xaxis=dict(
#                 title='Creation time',
#                 # gridcolor='rgb(255, 255, 255)',
#                 # # range=[2.003297660701705, 5.191505530708712],
#                 # # # type='log',
#                 # zerolinewidth=1,
#                 # ticklen=5,
#                 # gridwidth=2,
#             ),
#             yaxis=dict(
#                 title='Last activity',
#                 # gridcolor='rgb(255, 255, 255)',
#                 # # range=[36.12621671352166, 91.72921793264332],
#                 # zerolinewidth=1,
#                 # ticklen=5,
#                 # gridwidth=2,
#             ),
#             paper_bgcolor='rgb(243, 243, 243)',
#             plot_bgcolor='rgb(243, 243, 243)',
#         )

#         fig = go.Figure(data=[trace], layout=layout)
#         py.plot(fig, filename='items-cluster')

def main():
	# borrar siguiente linea para cerrar el programa al cerrar la grafica
	while not plt.fignum_exists(1):
		try:
			clusters = pd.read_csv(settings.active_clusters_csv)
		except:
			pass
		else:
			clusters["created_at"] = clusters["created_at"].apply(lambda x: (pd.to_datetime(x)))
			clusters["last_activity"] = clusters["last_activity"].apply(lambda x: (pd.to_datetime(x)))
			legends = []
			for _, cluster in clusters.iterrows():
				root_item = str(cluster.root_item)
				n=70
				if len(root_item)>n:
					root_item = root_item[:n+root_item[n:].find(" ")]+"\n"+root_item[n+root_item[n:].find(" ")+1:]
				terms = str(cluster.terms)
				if len(terms)>n:
					terms = terms[:n+terms[n:].find(" ")]+"\n"+terms[n+terms[n:].find(" ")+1:]
				legends.append("Cluster ID: "+str(cluster.id)+"\nitems: "+
								str(cluster.n_items)+"\nTerms: "+terms+
								"\nRoot item: "+root_item+
								"\nRoot_user: "+str(cluster.root_user)+
								"\nRoot_followers: "+str(cluster.root_followers)+
								"\nRoot_user_created_at: "+str(cluster.root_user_created_at)+
								"\nOther: "+str(cluster.other_items[:300]+"..."))

			plotter = ClusterPlotter()
			plotter.plot(x=clusters["created_at"], y=clusters["last_activity"], 
							sizes=1*clusters["n_items"],
							text=legends, 
							plot_at=str(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")))

if __name__ == '__main__':
    main()