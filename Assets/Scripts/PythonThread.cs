using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;


namespace VRSketch3
{
    public class PythonThread
    {
        public delegate void SignalErrorDelegate([In, MarshalAs(UnmanagedType.LPWStr)] string error);
        public delegate void UpdateDelegate(int index, int kind,
            [In, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 3)] float[] data, int data_count);
        public delegate void ApproxPlaneDelegate(
            [In, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 1)] float[] points, int coord_count,
            [Out, MarshalAs(UnmanagedType.LPArray, SizeConst = 4)] float[] plane);
        public delegate void ShowMenuDelegate(int controller_num,
            [In, MarshalAs(UnmanagedType.LPWStr)] string menu);

        [DllImport("PyUnityVR_cffi", CharSet = CharSet.Unicode)]
        public static extern int pyunityvr_init(SignalErrorDelegate error, UpdateDelegate update,
                                                ApproxPlaneDelegate approx_plane, ShowMenuDelegate show_menu);

        [DllImport("PyUnityVR_cffi")]
        public static extern int pyunityvr_frame(int num_ctrls, [In, MarshalAs(UnmanagedType.LPArray)] float[] controllers);

        [DllImport("PyUnityVR_cffi")]
        public static extern int pyunityvr_click([In, MarshalAs(UnmanagedType.LPWStr)] string id);

        [DllImport("PyUnityVR_cffi")]
        public static extern int pyunityvr_manual_enter(int token, float value);


        /***********************************************************************************************/


        SignalErrorDelegate keepalive_error;
        UpdateDelegate keepalive_update;
        ApproxPlaneDelegate keepalive_approx_plane;
        ShowMenuDelegate keepalive_show_menu;

        public delegate void PythonThreadDelegate();
        public delegate void MainThreadDelegate(WorldScript ws);

        List<PythonThreadDelegate> run_in_thread;
        int num_controllers;
        float[] raw_controllers;

        List<MainThreadDelegate> pending_updates;


        public PythonThread()
        {
            /* constructor, executes in main thread */
            run_in_thread = new List<PythonThreadDelegate>();
            pending_updates = new List<MainThreadDelegate>();
            new Thread(ExecutePythonThread).Start();
            RunInPythonThread(() =>
            {
                /* the delegate object themselves must remain alive for the duration of the whole run! */
                keepalive_error = CB_SignalError;
                keepalive_update = CB_Update;
                keepalive_approx_plane = CB_ApproxPlane;
                keepalive_show_menu = CB_ShowMenu;

                if (pyunityvr_init(keepalive_error, keepalive_update, keepalive_approx_plane,
                                   keepalive_show_menu) != 42)
                    Debug.LogError("pyunityvr_init() failed!");
            });
        }

        void RunInPythonThread(PythonThreadDelegate pt_delegate)
        {
            /* executes in main thread, requests a delegate to be called
             * in the python thread */
            lock (run_in_thread)
            {
                run_in_thread.Add(pt_delegate);
            }
        }

        void RunInMainThread(MainThreadDelegate pt_delegate)
        {
            /* executes in the python thread, requests a delegate to be called
             * in the main thread */
            lock (pending_updates)
            {
                pending_updates.Add(pt_delegate);
            }
        }

        public void RequestFrame(int num_ctrls, float[] raw_ctrls)
        {
            /* call this from the main thread */
            RunInPythonThread(() => {
                num_controllers = num_ctrls;
                raw_controllers = raw_ctrls;
            });
        }

        public void RequestClick(string menu_item)
        {
            /* call this from the main thread */
            RunInPythonThread(() => {
                if (pyunityvr_click(menu_item) != 42)
                    Debug.LogError("pyunityvr_click() failed!");
            });
        }

        public void RequestManualEnter(int token, float value)
        {
            /* call this from the main thread */
            RunInPythonThread(() => {
                if (pyunityvr_manual_enter(token, value) != 42)
                    Debug.LogError("pyunityvr_manual_enter() failed!");
            });
        }

        public MainThreadDelegate[] NextUpdatesBatch()
        {
            MainThreadDelegate[] result;

            lock (pending_updates)
            {
                result = pending_updates.ToArray();
                pending_updates.Clear();
            }
            return result;
        }

        void ExecutePythonThread()
        {
            /* main loop of the python thread */
            while (true)
            {
                PythonThreadDelegate[] pending;

                lock (run_in_thread)
                {
                    pending = run_in_thread.ToArray();
                    run_in_thread.Clear();
                }
                if (pending.Length == 0)
                {
                    Thread.Sleep(1);
                    continue;
                }

                foreach (var pt_delegate in pending)
                    pt_delegate();

                if (raw_controllers != null)
                {
                    if (pyunityvr_frame(num_controllers, raw_controllers) != 42)
                        Debug.LogError("pyunityvr_frame() failed!");
                    raw_controllers = null;
                }
            }
        }

        static void CB_SignalError(string error)
        {
            /* callback from python, runs in the python thread */
            if (error.StartsWith("INFO:"))
            {
                Debug.Log(error.Substring(5));
            }
            else
            {
                Debug.LogError(error);
#if UNITY_EDITOR
                UnityEditor.EditorApplication.Beep();
#endif
            }
        }

        void CB_Update(int index, int kind1, float[] data, int data_count)
        {
            /* callback from python, runs in the python thread */
            RunInMainThread((ws) => ws.ApplyPendingUpdate(index, kind1, data));
        }

        static void CB_ApproxPlane(float[] points, int coord_count, float[] plane)
        {
            /* callback from python, runs in the python thread */
            Vector3[] pts = new Vector3[coord_count / 3];
            for (int i = 0; i < pts.Length; i++)
                pts[i] = new Vector3(points[3 * i],
                                     points[3 * i + 1],
                                     points[3 * i + 2]);
            Plane result = VRSketch3.PlaneRecomputer.RecomputePlane(pts);
            plane[0] = result.normal.x;
            plane[1] = result.normal.y;
            plane[2] = result.normal.z;
            plane[3] = result.distance;
        }

        void CB_ShowMenu(int controller_num, string menu_string)
        {
            /* callback from python, runs in the python thread */
            RunInMainThread((ws) => ws.ShowMenu(controller_num, menu_string));
        }
    }
}
