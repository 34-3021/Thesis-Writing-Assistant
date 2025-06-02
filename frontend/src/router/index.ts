import {createRouter, createWebHistory} from "vue-router";

import Login from '@/pages/Login.vue';
import Index from "@/pages/Index.vue";
import Test from "@/pages/Test.vue";
import WritingAssistant from '@/pages/WritingAssistant.vue';  // 新增导入
import CheckUserInfo from "@/components/CheckUserInfo.vue";
import Profile from "@/components/Profile.vue";
import AddUser from "@/components/AddUser.vue";
import Chat from "@/components/Chat.vue";
import Register from "@/pages/Register.vue";
import PaperLibrary from '@/pages/PaperLibrary.vue';

const routes =
    [
        {
            path: '/',
            name: 'Login',
            component: Login
        },
        {
            path: '/register',
            name: 'Register',
            component: Register
        },
        {
            path: '/index',
            name: 'Index',
            component: Index,
            children: [
                {
                    path: '',
                    name:'IndexMain',
                    component: Profile,
                },
                {
                    path: 'checkUserInfo/:username',
                    name: 'checkUserDetail',
                    component: Profile,
                    props: true
                },
                {
                    path: 'checkUserInfo',
                    component: CheckUserInfo,
                },
                {
                    path: 'addUser',
                    component: AddUser,
                },
                {
                    path: 'chat',
                    component: Chat,
                },
                {
                    path: 'paper-library',
                    name: 'PaperLibrary',
                    component: PaperLibrary,
                },
            ]

        },
        {
            path: '/test',
            name: 'Test',
            component: Test
        },
        {
            path: '/writing-assistant',  // 新增路由路径
            name: 'WritingAssistant',
            component: WritingAssistant
        },
        {
            path: '/batch-qa',
            name: 'BatchQA',
            component: () => import('@/pages/BatchQA.vue')
        },
    ];

const router = createRouter({
    history: createWebHistory(),
    routes
});

export default router;
