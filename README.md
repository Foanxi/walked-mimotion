# mimotion

![ 刷步数](https://github.com/TonyJiangWJ/mimotion/actions/workflows/run.yml/badge.svg)
[![GitHub forks](https://img.shields.io/github/forks/TonyJiangWJ/mimotion?style=flat-square)](https://github.com/TonyJiangWJ/mimotion/forks)
[![GitHub stars](https://img.shields.io/github/stars/TonyJiangWJ/mimotion?style=flat-square)](https://github.com/TonyJiangWJ/mimotion/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/TonyJiangWJ/mimotion?style=flat-square)](https://github.com/TonyJiangWJ/mimotion/issues)

## 小米运动自动刷步数（支持邮箱登录）

- 小米运动自动刷步数，小米运动APP现已改名 `Zepp Life`，为方便说明，后面还是称其为小米运动。但下载注册时请搜索 `Zepp Life`。
- 注册账号后建议先去以下网站测试自己的账号刷步数是否正常（注意这些网站只是网络上收集的，不保证安全和有效性）：
    - https://steps.hubp.de/ 提示密码错误时可以多试几次 或者切换网络
    - https://bs.yanwan.store/run4/ 验证码001或998
- 如无法刷步数同步到支付宝等，建议重新注册一个新的。

## 新注册账号使用方法

由于新注册账号没有绑定过手环，会导致华米拦截向微信同步步数，此时你需要做的就是绑定一次小米1-7代任意手环即可。如果没有可以参考以下步骤：
- 前往 `https://bs.yanwan.store/run4/` 网站执行一次步数同步
- 该网站会自动为你账号绑定一个虚拟设备（感谢该建站大佬）
- 你可以在你 Zepp Life 中看到这个虚拟的设备
- 然后按照以下步骤进行配置即可成功同步了

### 如果觉得好用，请给一个免费的[star](https://github.com/TonyJiangWJ/mimotion/)吧

## Github Actions 部署指南

### 一、Fork 此仓库，然后创建token

#### 创建小权限的限时token，推荐

- 前往[https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)
  创建个人token，建议使用Fine-grained tokens，避免token泄露导致不必要的麻烦。
- 填写token的名称，用于自己区别干嘛用的。
- 选择token有效期，最大时长为1年。一年后需要重新续期或重建，唯一缺点
- `Repository access` 选择 `Only select repositories` 勾选自己fork后的仓库，下拉可搜索：输入 mimotion 进行检索
- 点击 `Repository permissions` 展开菜单，并勾选以下四个权限即可，其他的可以不勾选
    - `Actions` Access: `Read and write` 用于获取Actions的权限
    - `Contents` Access: `Read and write` 用于更新定时任务和日志文件的权限
    - `Metadata` Access: `Read-only` 这个自带的必选
    - `Workflows` Access: `Read and write` 获取用于更新 `.github/workflow` 下文件的权限

#### 你也可以创建更大权限的不限时token

- 建议使用上面的小权限token，这个token无法指定某一个仓库的权限，也就是token一旦泄露将有可能导致其他人直接自由访问和修改你的所有仓库代码
- 前往[https://github.com/settings/tokens/new](https://github.com/settings/tokens/new)创建
- 填写token名称，选择有效期
- `Select scopes` 勾选 `repo` 和 `workflow` 即可

#### 创建完毕后点击最底下的 `Generate token` 即可生成token，复制token并自己保存一下以备后续使用，关闭当前页面后将无法再看到它。

### 二、设置账号密码

#### 前往仓库设置创建变量

- Settings-->Secrets and variables-->Actions-->New repository secret
-
快捷跳转地址 [https://github.com/${你的github用户名}/mimotion/settings/secrets/actions](../../settings/secrets/actions)
- 点击右侧的 `New repository secret` 即可添加Secret

#### 添加名为 **PAT** 的Secret变量，值为第一步申请的token

- `PAT` 的作用是拿来更新随机执行时间以及加密token数据的，为了保证正常使用，一定要配置正确。

#### 添加名为 **AES_KEY** 的Secret变量，请自行创建一个长度为16个字符的字符串作为密钥

- 注意：密钥不要用中文，长度一定要是16个字符，否则可能出错。
- 如果你有多个账号，或者希望程序自动保存登录信息，就需要设置这个 `AES_KEY`。设置之后，程序会用这个密钥把各个账号的登录token信息加密保存起来。**请一定保管好你的密钥，不要泄露。**
- 同时，请确保你已经正确配置了 PAT 密钥，否则程序无法自动保存和提交信息到仓库。
- 第一次配置 `AES_KEY` 后，运行时可能会看到提示：“密钥不正确或者加密内容损坏 放弃token”，**这是正常现象**。因为原来加密文件用的是我的密钥，和你设置的不同，所以会提示不匹配。你直接忽略它，等程序运行完后，就会用你的新密钥生成一份新的加密文件，下次运行就正常了。
- 配置 `AES_KEY` 后，每个人的仓库里面到会保存一份 `encrypted_tokens.data`。每次更新代码时，这个文件会被覆盖。**为了避免丢失你保存的信息，请在更新代码前备份这个文件**，等代码更新完，再把它放回仓库并提交，最后重新运行workflow。

#### 添加名为 **CONFIG** 的Secret变量

- 需要注意Secret变量是密文，提交后无法查看，只能删除或用新值更新，建议本地保存一下自己的配置数据方便后期修改。或者参考步骤八导出配置数据。
- CONFIG的内容：

  ```json
  {
    "USER": "abcxxx@xx.com",
    "PWD": "password",
    "MIN_STEP": "18000",
    "MAX_STEP": "25000",
    "PUSH_PLUS_TOKEN": "",
    "PUSH_PLUS_HOUR": "",
    "PUSH_PLUS_MAX": "30",
    "PUSH_WECHAT_WEBHOOK_KEY": "",
    "TELEGRAM_BOT_TOKEN": "",
    "TELEGRAM_CHAT_ID": "",
    "SLEEP_GAP": "5",
    "USE_CONCURRENT": "False"
  }
  ```

  | 字段名                     | 格式                                                                                                             |
  |-------------------------|----------------------------------------------------------------------------------------------------------------|
  | USER                    | 小米运动登录账号，仅支持小米运动账号对应的手机号或邮箱，不支持小米账号                                                                            |
  | PWD                     | 小米运动登录密码，仅支持小米运动账号对应的密码                                                                                        |
  | MIN_STEP                | 最小步数                                                                                                           |
  | MAX_STEP                | 最大步数，最大步数和最小步数随机范围随着时间线性增加，北京时间22点达到最大值                                                                        |
  | PUSH_PLUS_TOKEN         | 推送加的个人token,申请地址[pushplus](https://www.pushplus.plus/push1.html)，工作流执行完成后推送每个账号的执行状态信息，如没有则不要填写                |
  | PUSH_PLUS_HOUR          | 限制只在某个整点进行pushplus的推送，值为整数，比如设置21，则只在北京时间21点XX分执行时才进行pushplus的消息推送。如不设置或值非数字则每次执行后都会进行推送                       |
  | PUSH_WECHAT_WEBHOOK_KEY | 企业微信推送通知的key，企业微信webhook机器人推送全地址为：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={机器人的key}，这里配置{机器人的key} |
  | PUSH_PLUS_MAX           | 设置pushplus最大推送账号详情数，默认为30，超过30个账号将只推送概要信息：多少个成功多少个失败。因为数量太多会导致内容过长无法推送。具体最大值请自行调试                              |
  | TELEGRAM_BOT_TOKEN      | 设置telegram机器人的token，同时需要配置TELEGRAM_CHAT_ID，否则不会执行推送                                                            |
  | TELEGRAM_CHAT_ID        | 设置telegram的chatId，需要同时配置TELEGRAM_BOT_TOKEN，否则无法执行推送。关于这两个值如何获取，请前往官网查看。                                        |
  | SLEEP_GAP               | 多账号执行间隔，单位秒，如果账号比较多可以设置的短一点，默认为5秒                                                                              |
  | USE_CONCURRENT          | 是否使用多线程，实验性功能，未测试是否有效。账号多的可以试试，将它设置为True即可，启用后 `SLEEP_GAP` 将不再生效                                               |

### 三、多账户设置(如用不上请忽略)

- 多账户请用 **#** 分割 然后保存到变量 **USER** 和 **PWD**
- 理论上账户数量不受限制，但是实际要看github actions的资源和华米接口是否有限制，pushplus消息内容应该也有最大长度限制，反正具体上限请自行测试

#### 例如

```json
{
  "USER": "13800138000#13800138001",
  "PWD": "abc123qwe#abcqwe2",
  "MIN_STEP": "18000",
  "MAX_STEP": "25000",
  "PUSH_PLUS_TOKEN": "",
  "PUSH_PLUS_HOUR": ""
}
```

#### 注意 **#** 分隔的账号和密码数量必须匹配，否则将跳过执行

### 四、自定义启动时间

#### 两种方式自定义启动时间

##### 1、添加名为 `CRON_HOURS` 的Variables变量 `Settings-->Secrets and variables-->Actions-->New repository variables` 注意不是Secret

-
快捷跳转地址 [https://github.com/${你的github用户名}/mimotion/settings/variables/actions](../../settings/variables/actions)
    - 填写自动执行的时间，单位为小时，此处需要设置UTC时间，例如设置 `0,2,4,6,8,14` 则会在北京时间 `8,10,12,14,16,22` 点触发执行
- 添加完成后可以在Actions中手动触发：`Random Cron` 来触发替换，或者等下一次定时执行时它将会自动替换。

##### 2、编辑 **.github/workflows/run.yml** 中的cron表达式

- cron表达式格式如下: `分 小时 日期 月份 年份`
- github actions中执行时间为UTC时间，即**北京时间-8**，如果需要每天`8，10，12，14，16，22`
  点执行，则设置cron为`0 0,2,4,6,8,14 * * *`

  ```yaml
  on:
    schedule:
      - cron: '0 0,2,4,6,8,14 * * *'
  ```

- **注意** 如果已添加 `CRON_HOURS` 变量，则修改此文件的cron表达式会失效，在下次执行 `Random Cron`
  后表达式中小时的部分会被覆盖为 `CRON_HOURS` 配置的值

- 注意以上两种方式二选一即可，推荐直接使用方式1，变量值填写的是逗号分隔的数字，别乱填别的报错别找我！
- github actions 0点为执行高峰，排队可能会延后一两小时才执行，建议直接从2开始

### 五、手动触发测试工作流

- 前往Actions,左侧选择 `刷步数`
  ，快捷链接：[https://github.com/${你的github用户名}/mimotion/actions/workflows/run.yml](../../actions/workflows/run.yml)
- 新fork的仓库默认未启用工作流，进入Actions后点击 `I understand my workflows, go ahead and enable them`
  启用，然后左侧选择 `刷步数` 之后，再点击 `enable workflow` 启用工作流。请确保开启工作流，否则不会定时执行。
- 点击右侧的`Run workflow`触发执行，触发后刷新即可查看执行记录。验证是否正确配置并执行刷步数。

### 六、感谢列表

本项目基于 `https://github.com/xunichanghuan/mimotion(已被ban)`
和 [https://github.com/huangshihai/mimotion](https://github.com/huangshihai/mimotion) 项目修改，特此感谢

新版本登录需要加密，感谢[https://github.com/hanximeng/Zepp_API/blob/main/index.php](https://github.com/hanximeng/Zepp_API/blob/main/index.php)
里面提供的aes加密密钥。大家可以去给作者点个star

### 七、同步最新代码

- 点击仓库界面上的 `Sync fork`，找不到的话直接Ctrl+F网页查找
- 然后点击 `Update branch` 或者 `Discard xxx commits`等待同步完成即可，如有其他提示请自行按提示操作。请不要提交 **pull request**
- 当配置了 `AES_KEY` 之后，因为每个人的仓库里面到会保存一份 `encrypted_tokens.data`，更新代码会被覆盖。为了避免数据丢失，请提前备份，在更新完成后将它重新提交到仓库中，然后再触发workflow。
- 同步更新后请自己再次仔细阅读README，配置项目修改等请自行对比，更新后因为配置不正确导致无法运行请不要找我

### 八、忘记配置后的处理

- 当长时间没有使用或者忘记了配置，可以通过手动触发工作流来发送配置信息到企业微信通知中，或者telegram机器人，请务必配置在私有的企业微信或telegram群组中，避免密码等敏感信息泄露给别人
- 步骤：
  - 首先配置Secrets：`INSPECT_WECHAT_HOOK_KEY` 配置企业微信机器人的key，具体请参考企业微信机器人文档。
  - telegram配置Secrets：`INSPECT_TELEGRAM_BOT_TOKEN`和`INSPECT_TELEGRAM_CHAT_ID` 配置机器人的token和聊天chatId，具体请参考TelegramBot文档。
  - 然后点击Actions，左侧选择 `提取配置信息` 手动运行它，运行成功后，将配置信息发送到企业微信或telegram中。企业微信或者telegram的推送自己按需选择，如果都不配置，请使用日志打印的方式。
- 如果没有企业微信或telegram，可以配置Secrets: `INSPECT_AES_KEY` 注意是16位的字符串，请勿使用弱密码，避免被人猜到。
  - 在Secrets中配置后，运行上述的Actions，然后在执行结果中查看日志打印的base64字符串。
  - 提取base64字符串后，可以使用在线AES加解密网站进行解密，加密方式为CBC，填充方式为PKCS7，密钥长度128bit，密钥和偏移量（iv）均为INSPECT_AES_KEY
  - 可用网站：https://www.toolhelper.cn/SymmetricEncryption/AES
- 以上两种方式都可以提取 CONFIG，PAT，AES_KEY 三个Secrets配置，请自行选择。

## 注意事项

1. 默认每天运行6+次，由run.yml中的cron控制，分钟为随机值，执行后自动更新分钟值，随机后可能当前整点二次执行，例如：8:
   05分执行后，分钟值随机为50，则会在8:50再次执行。

- 如果配置了 `CRON_HOURS` Variable变量，则脚本将自动判断，例如8:05分执行后，将从小时中剔除8，即8:00-8:59都不会再重复执行，避免随机的步数混乱。

2. 多账户的数量和密码请一定要对上 不然无法使用!!!

3. 启动时间得是UTC时间!

4. 如果支付宝没有更新步数，到小米运动->设置->账号->注销账号->清空数据，然后重新登录，重新绑定第三方。建议去开头提到的网站测试账号是否正常

5. 小米运动不会更新步数，只有关联的会同步！！！！！

6. 请各位在使用时Fork[当前仓库](https://github.com/TonyJiangWJ/mimotion/)，防止出现不必要的bug.

7. 请注意，账号不是 [小米账号]，而是 [小米运动/ZeppLife] 的账号。

8. 最大步数和最小步数随着时间增长，10点执行时范围为10/22 \* 18000 ~ 10/22 \* 25000：8181 ~
   11363，以此类推，在北京时间22点达到最大值，即22点执行时随机步数的范围为18000-25000之间。要修改这个范围可以修改CONFIG中的MIN_STEP和MAX_STEP。

9. cron的执行根据github actions的资源进行排队，并不是百分百按指定的时间进行运行，请知悉。

10. 新版本接口有限制，同ip登录过多账号可能会429，请自行测试。

### 查看执行记录

- 前往 [Actions](../../actions) 可以查看所有工作流的执行历史
    - `刷步数 #41: Scheduled` 代表是定时任务触发，`刷步数 #33: Manually run by xxx` 代表手动触发
- 点击其中一条记录，可以查看执行详情，这里以 `刷步数` 为例：
    - 详情界面 `Jobs` 可以查看到一个 `build` ，点击它查看执行步骤
    - 执行步骤中主要关注 `开始` ，点击 `开始` 展开详情
    - 展开后便可以查看到执行日志，如果执行成功，则会显示每个账号当前随机的步数是多少
    - 如果执行失败，则需要根据实际情况分析具体失败原因
- 对于随机Cron的工作流 `Random Cron`，它会在 `刷步数` 执行成功后触发，执行后会更新cron表达式创建随机的分钟值，然后提交到git仓库。这一步失败的主要原因有：
    - `PAT` Secret变量，也就是个人token设置的不正确
    - `CRON_HOURS` Variable变量设置的不正确，需要逗号分隔的小时字符串例如：`1,3,4,5,6,7` 。不要添加奇奇怪怪的东西
    - 其他请见执行日志
- 随机Cron运行完毕后可以查看 `cron_change_time` 文件的内容，记录了触发方式、当前触发时间、cron表达式信息、下一次定时触发时间等信息，示例如下：
  ```log
  trigger by: workflow_run
  current system time:
  UTC: 23-06-03 12:56:53
  北京时间: 23-06-03 20:56:53
  current cron:
  UTC时间: '48 1,4,7,10,12,14 * * *'
  北京时间: '48 9,12,15,18,20,22 * * *'
  next cron:
  UTC时间: '37 1,4,7,10,12,14 * * *'
  北京时间: '37 9,12,15,18,20,22 * * *'
  next exec time: UTC(14:37) 北京时间(22:37)
  ```

## 本地开发

复制 `.env.example` 文件为 `.env`，并在 `.env` 中填入你的配置信息
```shell
cp .env.example .env
```
**注意**：`.env` 文件已添加到 .gitignore 中，请不要推送到代码仓库中以免造成数据泄露

创建 python 虚拟环境
```shell
python3 -m venv venv
```

激活虚拟环境
```shell
# Windows
./venv/Script/Activate

# Linux
source ./venv/bin/activate
```

安装依赖
```shell
pip install -r requirements.txt
```

执行脚本修改步数
```shell
python3 main.py
```

## 可视化页面（Web UI）

仓库新增了 `web_app.py`（Flask）+ `templates/`，可以在页面上直接输入步数并立即修改。
**配置完全复用现有配置**：优先环境变量 `CONFIG`(JSON)，其次 `USER`+`PWD`，也支持根目录 `.env`；
登录态依旧用 `AES_KEY` 加密保存在 `encrypted_tokens.data`。

### 页面能力

- 账号列表自动从配置读取并脱敏展示，可勾选要修改的账号，也可给单个账号单独指定步数（留空则跟随全局步数）
- 步数模式：自定义步数 / 按时间随机（与定时任务逻辑一致，北京时间22点达到 `MAX_STEP`）
- 多账号串行执行，间隔沿用配置中的 `SLEEP_GAP`，避免接口 429
- 执行日志实时输出，执行完成后沿用 `AES_KEY` 加密保存登录态

### 本地启动

```shell
pip install -r requirements.txt
python3 web_app.py            # 默认 http://127.0.0.1:8888
PORT=8080 python3 web_app.py  # 换端口
```

复制 `.env.example` 为 `.env` 后填写（字段与 `main.py` 完全一致，只多了可选的 `WEB_PASSWORD`）：

```shell
cp .env.example .env
```

```shell
CONFIG={"USER":"abc@xx.com","PWD":"password","MIN_STEP":"18000","MAX_STEP":"25000","SLEEP_GAP":"5"}
AES_KEY=1234567890abcdef
WEB_PASSWORD=你的访问口令
```

> 公网部署请务必设置 `WEB_PASSWORD`，否则任何人打开页面就能改你的步数。未设置时页面不做登录校验，方便本地使用。
> 页面只做步数修改，不会改动仓库里的定时任务；定时任务仍由 GitHub Actions 正常执行，两者共用同一份登录态文件。

### 快速部署

#### 1. 源码一键部署（推荐，服务器不需要 Docker）

脚本会自动：安装 python3 依赖 → 同步代码 → 建虚拟环境 → 写 systemd 服务并开机自启。

```shell
# 在本机把仓库传到服务器（服务器上不需要 git）
rsync -av --exclude '.git' --exclude 'venv' ./ root@服务器IP:/tmp/mimotion/

# 登录服务器执行
ssh root@服务器IP
cd /tmp/mimotion
cp .env.example .env && vi .env        # 填 CONFIG（或 USER/PWD）、AES_KEY、WEB_PASSWORD
sudo ./deploy/install.sh               # 默认 /opt/mimotion，端口 8888
# 自定义：sudo ./deploy/install.sh /opt/mimotion 9000
```

脚本结束会给出访问地址与常用命令：

```shell
systemctl status mimotion-web          # 查看状态
journalctl -u mimotion-web -f          # 看实时日志
systemctl restart mimotion-web         # 改完 .env 后重启
```

> 支持 Ubuntu / Debian / CentOS / RHEL，x86_64 与 ARM 都可用；服务由 `waitress` 提供，无需 gunicorn。
> 记得在防火墙/云厂商安全组放行端口：`ufw allow 8888/tcp`。

#### 2. Docker Compose（服务器已装 Docker 时，含登录态持久化）

```shell
cp .env.example .env && vi .env
docker compose up -d --build
# 访问 http://服务器IP:5000 ，改端口改 docker-compose.yml 里的 "5000:5000" 左侧
docker compose logs -f
```

#### 3. 纯 Docker

```shell
docker build -t mimotion-web .
docker run -d --name mimotion-web --restart unless-stopped \
  -p 5000:5000 --env-file .env \
  -v $(pwd)/encrypted_tokens.data:/app/encrypted_tokens.data \
  mimotion-web
```

#### 4. Render / Railway / Koyeb / Heroku 等 PaaS

仓库已带 `Procfile`，直接新建 Web Service 并关联仓库即可（启动命令 `gunicorn web_app:app`）。
在平台的环境变量里配置 `CONFIG`（或 `USER`/`PWD`）、`AES_KEY`、`WEB_PASSWORD`。

> 注意：这类平台容器重启后文件系统会重置，`encrypted_tokens.data` 会丢失，程序会自动重新登录，不影响使用；
> 如需保留登录态请用 Docker 方式并挂载该文件。

#### 5. 可选：打包成单个二进制（服务器连 Python 都不想装时）

可视化页面可以打成**一个独立可执行文件**，拷上去直接跑。

```shell
# 方式一：在 Linux 服务器上直接打包（Mac 没有 Docker 时用这个，架构/glibc 天然匹配）
#         打包期间临时需要 python3，打完之后产物独立运行，可卸载 Python
./build.sh

# 方式二：本机有 Docker 时，用它打出 Linux x86_64 产物
./build.sh docker
# 产物在 dist/mimotion-web，约 20~30MB
```

> PyInstaller 不支持交叉编译，Linux 二进制必须在 Linux 环境里产出：
> 没有 Docker 就把仓库传到服务器跑 `./build.sh`，或在 GitHub Actions 里构建（两者都不需要本地装任何东西）。

拷到服务器运行：

```shell
scp dist/mimotion-web root@你的服务器:/opt/mimotion/
# 服务器上：把 .env 放到 /opt/mimotion/.env（CONFIG / AES_KEY / WEB_PASSWORD 等）
mkdir -p /opt/mimotion && cd /opt/mimotion
PORT=8888 ./mimotion-web
```

配置项（都是环境变量，也可写进同目录的 `.env`）：

| 变量 | 说明 |
|---|---|
| `PORT` | 监听端口，默认 `8888` |
| `HOST` | 监听地址，默认 `0.0.0.0` |
| `DATA_DIR` | 配置与登录态存放目录，设置后程序的 `.env`、`encrypted_tokens.data` 都读写这个目录（服务化部署建议设置） |
| `WEB_PASSWORD` | 访问口令，公网部署必填 |

systemd 常驻示例（`/etc/systemd/system/mimotion-web.service`）：

```ini
[Unit]
Description=mimotion web
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mimotion
Environment=PORT=8888
Environment=DATA_DIR=/opt/mimotion
Environment=WEB_PASSWORD=你的访问口令
ExecStart=/opt/mimotion/mimotion-web
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```shell
systemctl daemon-reload && systemctl enable --now mimotion-web
journalctl -u mimotion-web -f
```

二进制部署注意事项：

- **不能跨平台打包**：Linux 服务器请用 `./build.sh docker`；Windows 上本地打包需手动执行 `pyinstaller --onefile --add-data "templates;templates" ...`
- 产物基于 Debian bullseye（glibc 2.31），Ubuntu 20.04+ / Debian 11+ / CentOS 8+ 可直接运行；更老的系统（如 CentOS 7）请用 Docker 部署
- 单文件启动时会先解压到临时目录，首次启动约 1~3 秒，属正常现象
- 账号密码不会打进二进制里，全部来自环境变量/`.env`，换机器只需拷二进制 + `.env`

### 部署相关环境变量

| 变量 | 说明 |
|---|---|
| `PORT` | 监听端口，源码直跑默认 `8888`，Docker 内固定 `5000` |
| `HOST` | 监听地址，默认 `0.0.0.0` |
| `DATA_DIR` | 配置与登录态存放目录，设置后 `.env`、`encrypted_tokens.data` 都读写该目录（systemd 部署脚本已自动设置） |
| `WEB_PASSWORD` | 页面访问口令，公网部署必填；不设置则不做登录校验 |

健康检查接口：`GET /healthz`（Docker Compose 已内置该检查）。