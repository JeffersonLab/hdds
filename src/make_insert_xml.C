void make_insert_xml(){
  ofstream out("pwo.xml");

  double outer_left_y[40]
    ={-40.836,-38.7535,-36.633,-34.5415,-32.442,-30.343,-28.262,-26.154,-24.037,
      -21.931,
      -19.844,-17.730, -15.6585 ,-13.565,-11.4675,-9.385,-7.297,-5.213,-3.1025,
      -1.036,
      1.0545,3.139,5.231,7.337,9.4205,11.5655,13.674,15.6385,17.8425,20.031,
      22.096,24.188,26.284,28.407,30.476,32.5805,34.664,36.7555,38.8565,40.939};
  double outer_left_x[40]
    ={40.718,40.717,40.739,40.743,40.739,40.730,40.720,40.716,40.721,40.696,
      40.686,40.700,40.701,40.685,40.690,40.694,40.723,40.718,40.720,40.722,
      40.720,40.671,40.675,40.691,40.684,40.721,40.723,40.711,40.724,40.706,
      40.702,40.732,40.724,40.703,40.756,40.761,40.766,40.787,40.783,40.744};
  double outer_right_y[40]
    ={-40.705,-38.6075,-36.53,-34.3875,-32.307,-30.222,-28.122,-26.025,-23.924,
      -21.84,
      -19.733,-17.62, -15.5115 ,-13.42,-11.3375,-9.24,-7.148,-5.052,-2.9825,-0.86,
      1.2295,3.325,5.413,7.487,9.5835,11.6605,13.732,15.9475,17.9235,19.973,
      22.092,24.18,26.282,28.344,30.461,32.5565,34.653,36.7445,38.8235,40.927};
  double outer_right_x[40]
    ={-40.68,-40.666,-40.694,-40.688,-40.675,-40.690,-40.701,-40.718,-40.706,
      -40.729,
      -40.721,-40.743,-40.732,-40.716,-40.708,-40.724,-40.696,-40.698,-40.689,
      -40.713,
      -40.702,-40.701,-40.7,-40.718,-40.710,-40.691,-40.704,-40.7,-40.693,
      -40.681,
      -40.693,-40.691,-40.678,-40.657,-40.643,-40.638,-40.624,-40.618,-40.635,
      -40.629};
  double inner_left_x[2]={7.308,7.322};
  double inner_left_y[2]={-1.025,1.023};
  double inner_right_x[2]={-3.136,-3.129};
  double inner_right_y[2]={-1.047,1.044};

  double ymid[42],dphi[42]; 
  //double old=0.;
  //double dx_min=1e6;

  for (int i=0;i<40;i++){
    int ncopy=40;
    ymid[i]=0.5*(outer_left_y[i]+outer_right_y[i]);
    double dx=outer_left_x[i]-outer_right_x[i];
    dphi[i]=-180/M_PI*(outer_left_y[i]-outer_right_y[i])/dx;
    dx/=39.; // find module size
    if (i==19 || i==20) ncopy=19;

    //if (dx<dx_min) dx_min=dx;
    // Debug:
    //double dy=ymid[i]-old;
    //old=ymid[i];
    //cout << i << " " << ymid[i] << " " << dy <<endl;
    
    out << "  <composition name=\"XTrow"<<i<<"\">"<< endl;
    out << "    <mposX volume=\"XTModule\" ncopy=\""<< ncopy
	<< "\" X0=\"" << -outer_left_x[i] << "\" dX=\"" << dx <<"\">" <<endl;
    out << "      <column value=\"0\" step=\"1\"/>" <<endl;
    out << "      <row value=\""<<i<<"\"/>"<<endl;
    out << "    </mposX>" << endl;
    out << "  </composition>" << endl;
  }
  // Handle the right side half-width rows 
  ymid[40]=ymid[19];
  ymid[41]=ymid[20];
  dphi[40]=dphi[19];
  dphi[41]=dphi[20];
  for (int i=0;i<2;i++){
    double dx=-(outer_right_x[19+i]-inner_right_x[i])/18.;
    out << "  <composition name=\"XTrow"<<40+i<<"\">"<< endl;
    out << "    <mposX volume=\"XTModule\" ncopy=\"19\" X0=\""
	<< -inner_right_x[i] << "\" dX=\"" << dx <<"\">" <<endl;
    out << "      <column value=\"21\" step=\"1\"/>" <<endl;
    out << "      <row value=\""<<19+i<<"\"/>"<<endl;
    out << "    </mposX>" << endl;
    out << "  </composition>" << endl;
  }

  // cout << dx_min << endl;

  out << "  <composition name=\"CrystalECAL\">" << endl;
  out << "    <posXYZ volume=\"InsertBeamPipe\" X_Y_Z=\"0. 0.075 8.4095\"/>"
      << endl;
  out << "    <posXYZ volume=\"XTTA\" X_Y_Z=\"0. 0.075 -13.0\"/>" << endl;
  for (int i=0;i<42;i++){
    out << "    <posXYZ volume=\"XTrow"<<i<<"\" X_Y_Z=\"0. " << ymid[i] 
	<<" 0.\" rot=\"0 0 " << dphi[i] <<"\"/>" << endl;
  }

  out << "  </composition>" << endl << endl;
  

  out.close();
  
}
