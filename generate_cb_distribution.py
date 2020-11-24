# -*- coding: utf-8 -*-
# @Time : 2020/11/4 0:38
# @File : generate_cb_distribution.py
# @Author : Rocky C@www.30daydo.com

# 可转债价格分布图
import os
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from configure.settings import DBSelector,get_config_data
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar
import sys
from selenium import webdriver
from pyecharts.commons.utils import JsCode
from common.BaseService import BaseService


if sys.platform == 'win32':
    SELENIUM_PATH = r'C:\OneDrive\Tool\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'
    driver = None
else:
    SELENIUM_PATH = './phantomjs'
    driver = webdriver.PhantomJS(executable_path=SELENIUM_PATH)

def calc_statistics(pct):
    bigger = pct[pct >= 0].count()
    smaller = pct[pct < 0].count()
    max_id = pct.argmax()
    min_id = pct.argmin()
    avg = round(float(pct.mean()), 2)
    std = round(float(pct.std(ddof=1)), 2)
    return bigger, smaller, avg, std, max_id, min_id


def get_XY(bins, pct, label, color):
    # 分箱获取Y轴的数据

    result = pd.cut(pct, bins, ordered=True, labels=label)
    v = pd.value_counts(result)
    result_dict = {}
    for i in label:
        if i == "-90":
            j = '-20+'
        else:
            j = i
        result_dict[j] = v.loc[i]

    gte_20 = pct[pct >= 20].count()
    result_dict.update({'20+': gte_20})
    y_list = []
    for k, v in result_dict.items():
        if k.startswith('-'):
            color_ = color[0]
        else:
            color_ = color[1]

        y_list.append(opts.BarItem(
            name=str(v),
            value=int(v),
            itemstyle_opts=opts.ItemStyleOpts(color=color_),
        ))

    return result_dict, y_list


class CBDistribution(BaseService):
    def __init__(self):
        super(CBDistribution, self).__init__()
        root_path = get_config_data('data_path')
        self.IMGAGE_PATH = os.path.join(root_path,f"{self.today}_cb.png")
        self.HMTL_PATH = os.path.join(root_path,f"{self.today}_cb.html")

        self.check_path('data')

    def get_bond_data(self):
        DB = DBSelector()
        engine = DB.get_engine('db_stock', 'qq')

        df = pd.read_sql('tb_bond_jisilu', con=engine)
        return df

    def get_XY_data(self, df):
        bins = list(range(-20, 21))
        bins.insert(0, -90)
        bins.append(90)
        label = [str(b) for b in bins[:-1]]

        pct = df['可转债涨幅']
        pct_zg = df['正股涨跌幅']

        bigger, smaller, avg, std, max_id, min_id = calc_statistics(pct)

        max_name = df.loc[max_id]['可转债名称']
        max_pct = df.loc[max_id]['可转债涨幅']
        min_name = df.loc[min_id]['可转债名称']
        min_pct = df.loc[min_id]['可转债涨幅']

        color1 = ("#228B22", "#FF0000")
        color2 = ("#009ACD", "#F4A460")

        result_dict, zz_list = get_XY(bins, pct, label, color1)
        _, zg_list = get_XY(bins, pct_zg, label, color2)

        data = {
            'max_name': max_name,
            'max_pct': max_pct,
            'min_name':min_name,
            'min_pct': min_pct,
            'zz_list': zz_list,
            'zg_list': zg_list,
            'result_dict': result_dict

        }

        return data

    def generate_html(self):
        df = self.get_bond_data()
        data = self.get_XY_data(df)

        bigger= data['bigger']
        smaller= data['smaller']
        avg= data['avg']
        std= data['std']
        max_name= data['max_name']
        max_pct= data['max_pct']
        min_name= data['min_name']
        min_pct= data['min_pct']

        bar = (
            Bar()
                .add_xaxis(list(data['result_dict'].keys()))
                .add_yaxis(f"{self.today}-可转债价格分布", data['zz_list'], category_gap=3)
                .add_yaxis(f"{self.today}-正股价格分布", data['zg_list'], category_gap=3)
                .set_series_opts(
                label_opts=opts.LabelOpts(is_show=True),
                axispointer_opts=opts.AxisPointerOpts(is_show=True))
                .set_global_opts(
                title_opts=opts.TitleOpts(title="可转债价格分布"),
                xaxis_opts=opts.AxisOpts(
                    name="涨跌幅",
                    is_show=True,
                    name_rotate=30,
                ),
                graphic_opts=[
                    opts.GraphicGroup(
                        graphic_item=opts.GraphicItem(
                            left="70%",
                            top="20%",
                        ),
                        children=[

                            opts.GraphicText(
                                graphic_item=opts.GraphicItem(
                                    left="center",
                                    top="middle",
                                    z=100,
                                ),
                                graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                    text=JsCode(
                                        f"['涨幅>=0：{bigger}',"
                                        f"'涨幅<0：{smaller}',"
                                        f"'平均涨幅：{avg}%',"
                                        f"'波动方差：{std}',"
                                        f"'',"
                                        f"'最大：{max_name}  {max_pct}%',"
                                        f"'最小：{min_name}  {min_pct}%',"
                                        "''].join('\\n')"
                                    ),
                                    font="14px Microsoft YaHei",
                                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                                        fill="#333"
                                    )
                                )
                            )
                        ]
                    )
                ],
            )

        )

        bar.render(self.HMTL_PATH)
        # 自定义一个driver
        make_snapshot(snapshot, bar.render(), self.IMGAGE_PATH, driver=driver)


def main():
    app = CBDistribution()
    app.generate_html()


if __name__ == '__main__':
    main()
